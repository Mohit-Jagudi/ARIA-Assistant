"""
main.py
───────
ARIA FastAPI Backend — All API endpoints.
This is the central server that connects:
  - Gemini AI brain
  - Firebase real-time database
  - Twilio SMS alerts
  - All three frontend portals
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import time
import os
from dotenv import load_dotenv

from gemini_engine import (
    classify_crisis,
    assign_staff_roles,
    generate_guest_alert,
    generate_responder_briefing,
    generate_crisis_analysis
)
from firebase_client import (
    get_available_staff,
    get_guests_in_zone,
    create_crisis,
    update_crisis,
    close_crisis,
    add_crisis_timeline_event,
    update_staff_status,
    update_guest_safety,
    get_active_crises,
    get_all_staff,
    register_guest,
    update_staff_location
)
from alert_sender import (
    send_staff_alert,
    send_bulk_guest_alerts,
    send_manager_alert,
    send_responder_briefing
)

load_dotenv()

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ARIA — Adaptive Response Intelligence for Hospitality",
    description="AI-powered emergency coordination system by THE_PHOENIX",
    version="1.0.0"
)

# Allow all origins for hackathon demo
# In production: restrict to your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HOTEL_ID = os.getenv("HOTEL_ID", "hotel_grand_001")


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ══════════════════════════════════════════════════════════════════════════════

class CrisisReport(BaseModel):
    report: str                          # Raw text from staff/guest
    reported_by: str                     # staff_id or "guest_room_412"
    reporter_location: Optional[str] = None

class GuestRegistration(BaseModel):
    room: str
    name: str
    phone: str
    language: str                        # "en", "hi", "ja", "ar", "fr", etc.
    floor: int

class StaffLocationUpdate(BaseModel):
    staff_id: str
    location: str
    floor: int

class TaskStatusUpdate(BaseModel):
    staff_id: str
    crisis_id: str
    status: str                          # "on_my_way" | "reached" | "completed"

class GuestSafetyResponse(BaseModel):
    room: str
    crisis_id: str
    status: str                          # "safe" | "needs_help"

class CrisisClose(BaseModel):
    crisis_id: str
    resolved_by: str


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "system": "ARIA",
        "status": "operational",
        "team": "THE_PHOENIX",
        "members": ["Prikshit", "Mohit"]
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": int(time.time())}


# ══════════════════════════════════════════════════════════════════════════════
# CRISIS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/crisis/report")
async def report_crisis(report: CrisisReport):
    """
    THE MAIN ENDPOINT — Called when anyone reports an emergency.

    What happens in order:
    1. Gemini classifies the crisis (3 seconds)
    2. Crisis record created in Firebase
    3. Available staff fetched
    4. Gemini assigns tasks to each staff member
    5. SMS alerts sent to all staff
    6. Affected guests identified by floor
    7. Multilingual SMS alerts sent to all guests
    8. Manager alerted
    9. Everything logged to Firebase timeline

    Returns complete crisis record with all assignments.
    """
    start_time = time.time()

    # ── STEP 1: Classify crisis with Gemini ───────────────────────────────────
    print(f"\n🧠 Classifying crisis: '{report.report}'")
    try:
        crisis = classify_crisis(report.report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini classification failed: {str(e)}")

    print(f"✅ Classified as: {crisis['crisis_type']} | Severity: {crisis['severity']}")

    # ── STEP 2: Create crisis in Firebase ─────────────────────────────────────
    crisis_record = {
        **crisis,
        "reported_by": report.reported_by,
        "reporter_location": report.reporter_location,
        "status": "active",
        "created_at": int(time.time()),
        "staff_assignments": [],
        "guest_alerts_sent": 0,
        "guests_safe": 0,
        "guests_need_help": 0,
        "guests_unknown": 0
    }

    crisis_id = create_crisis(crisis_record)
    print(f"✅ Crisis created in Firebase: {crisis_id}")

    add_crisis_timeline_event(
        crisis_id,
        f"Crisis reported: {crisis['crisis_type']} at {crisis['location']}",
        report.reported_by
    )

    # ── STEP 3: Get available staff ────────────────────────────────────────────
    available_staff = get_available_staff()
    print(f"✅ Available staff: {len(available_staff)}")

    # # ── STEP 4: Assign roles ──────────────────────────────────────────────────
    assignments = []
    if available_staff:
        try:
            assignments = assign_staff_roles(crisis, available_staff)
        except Exception as e:
            print(f"⚠️ Role assignment failed: {e}")
            assignments = []

    # ── STEP 5: Update Firebase + count assignments ───────────────────────────
    staff_results = []
    for assignment in assignments:
        assigned_id = assignment.get("staff_id")
        
        # Match by either 'id' or 'staff_id' key
        staff_info = next(
            (s for s in available_staff 
             if s.get("id") == assigned_id or assigned_id in s.get("id", "")),
            None
        )
        
        # If Gemini returned wrong ID, just use first available staff
        if not staff_info and available_staff:
            staff_info = available_staff[len(staff_results) % len(available_staff)]

        if staff_info:
            real_id = staff_info.get("id", assigned_id)
            update_staff_status(real_id, "assigned", assignment["task"])
            
            add_crisis_timeline_event(
                crisis_id,
                f"Staff {assignment['name']} assigned: {assignment['task'][:50]}",
                "ARIA"
            )

            staff_results.append({
                "staff_id": real_id,
                "name": assignment.get("name", staff_info.get("name", "Staff")),
                "task": assignment["task"],
                "sms_sent": False
            })

    update_crisis(crisis_id, {"staff_assignments": staff_results})
    print(f"✅ {len(staff_results)} staff assigned")

    # ── STEP 6: Get affected guests by floor ──────────────────────────────────
    affected_guests = get_guests_in_zone(crisis.get("affected_floors", []))
    print(f"✅ Guests in affected zone: {len(affected_guests)}")

    # ── STEP 7: Generate + send multilingual guest alerts ─────────────────────
    guest_messages = {}
    for guest in affected_guests:
        room = guest.get("room")
        language = guest.get("language", "en")
        try:
            message = generate_guest_alert(crisis, language, room)
            guest_messages[room] = message
        except Exception as e:
            # Fallback to English if translation fails
            guest_messages[room] = generate_guest_alert(crisis, "en", room)

    alert_results = send_bulk_guest_alerts(affected_guests, guest_messages)

    update_crisis(crisis_id, {
        "guest_alerts_sent": alert_results["sent"],
        "guests_unknown": len(affected_guests)
    })

    add_crisis_timeline_event(
        crisis_id,
        f"Guest alerts sent: {alert_results['sent']} successful, {alert_results['failed']} failed",
        "ARIA"
    )

    # ── STEP 8: Alert manager ─────────────────────────────────────────────────
    # Find manager in staff list
    all_staff = get_all_staff()
    manager = next(
        ({"phone": d["phone"], **d} for d in all_staff.values()
         if d.get("role") == "manager"),
        None
    )

    if manager:
        send_manager_alert(
            phone=manager["phone"],
            crisis_type=crisis["crisis_type"],
            severity=crisis["severity"],
            location=crisis["location"],
            staff_count=len(staff_results),
            guest_count=alert_results["sent"]
        )

    # ── DONE ──────────────────────────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 2)
    print(f"\n✅ CRISIS COORDINATED in {elapsed} seconds")

    return {
        "crisis_id": crisis_id,
        "classification": crisis,
        "staff_assigned": len(staff_results),
        "guests_alerted": alert_results["sent"],
        "response_time_seconds": elapsed,
        "status": "active",
        "message": f"ARIA coordinated response in {elapsed}s"
    }


@app.get("/crisis/active")
def get_active():
    """Returns all active crises — used by manager dashboard."""
    return get_active_crises()


@app.post("/crisis/close")
def close_active_crisis(data: CrisisClose):
    """
    Manager marks crisis as resolved.
    Triggers post-crisis learning analysis.
    """
    from firebase_client import db, HOTEL_ID
    from firebase_admin import db as fdb

    # Get crisis data before closing
    crisis_ref = fdb.reference(f"/hotels/{HOTEL_ID}/active_crises/{data.crisis_id}")
    crisis_data = crisis_ref.get()

    if not crisis_data:
        raise HTTPException(status_code=404, detail="Crisis not found")

    # Add resolution info
    crisis_data["resolved_at"] = int(time.time())
    crisis_data["resolved_by"] = data.resolved_by

    # Generate learning analysis
    try:
        analysis = generate_crisis_analysis(crisis_data)
        crisis_data["learning_analysis"] = analysis
    except Exception as e:
        print(f"⚠️ Analysis generation failed: {e}")
        crisis_data["learning_analysis"] = None

    # Close in Firebase (moves to history)
    close_crisis(data.crisis_id)

    # Free up all assigned staff
    all_staff = get_all_staff()
    for staff_id in all_staff:
        update_staff_status(staff_id, "available")

    return {
        "status": "resolved",
        "crisis_id": data.crisis_id,
        "analysis": crisis_data.get("learning_analysis")
    }


# ══════════════════════════════════════════════════════════════════════════════
# STAFF ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/staff/all")
def get_staff():
    """Returns all staff — used by manager dashboard."""
    return get_all_staff()

@app.post("/staff/location")
def update_location(data: StaffLocationUpdate):
    """Staff checks in from their current location."""
    update_staff_location(data.staff_id, data.location)
    return {"status": "updated", "staff_id": data.staff_id, "location": data.location}

@app.post("/staff/task-status")
def update_task(data: TaskStatusUpdate):
    """Staff updates their task status (on the way / reached / done)."""
    add_crisis_timeline_event(
        data.crisis_id,
        f"Staff {data.staff_id}: {data.status}",
        data.staff_id
    )

    if data.status == "completed":
        update_staff_status(data.staff_id, "available")

    return {"status": "updated"}


# ══════════════════════════════════════════════════════════════════════════════
# GUEST ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/guest/register")
def register(data: GuestRegistration):
    """Called at hotel check-in. Registers guest + sends welcome SMS."""
    register_guest(data.room, data.name, data.phone, data.language, data.floor)

    # Send welcome message
    from alert_sender import send_sms
    welcome = (
        f"🏨 Welcome to Hotel Grand, {data.name}!\n\n"
        f"You're protected by ARIA — our AI emergency system.\n\n"
        f"In any emergency:\n"
        f"1. Stay calm\n"
        f"2. Check your phone for instructions\n"
        f"3. Follow ARIA's guidance\n\n"
        f"Room: {data.room} | Keep your phone nearby.\n"
        f"ARIA is watching over you. 🛡️"
    )
    send_sms(data.phone, welcome)

    return {"status": "registered", "room": data.room}


@app.post("/guest/safety-response")
def guest_safety(data: GuestSafetyResponse):
    """Guest marks themselves as safe or requests help."""
    update_guest_safety(data.room, data.status)

    # Update crisis guest counts
    from firebase_client import get_active_crises
    crises = get_active_crises()

    if data.crisis_id in crises:
        crisis = crises[data.crisis_id]
        if data.status == "safe":
            update_crisis(data.crisis_id, {
                "guests_safe": crisis.get("guests_safe", 0) + 1,
                "guests_unknown": max(0, crisis.get("guests_unknown", 1) - 1)
            })
        elif data.status == "needs_help":
            update_crisis(data.crisis_id, {
                "guests_need_help": crisis.get("guests_need_help", 0) + 1,
                "guests_unknown": max(0, crisis.get("guests_unknown", 1) - 1)
            })

            add_crisis_timeline_event(
                data.crisis_id,
                f"⚠️ Guest in {data.room} needs help — dispatch staff immediately",
                "GUEST_RESPONSE"
            )

    return {"status": "recorded", "room": data.room, "response": data.status}


# ══════════════════════════════════════════════════════════════════════════════
# FIRST RESPONDER ENDPOINT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/responder/brief/{crisis_id}")
def send_briefing(crisis_id: str, responder_phone: str, service_type: str):
    """
    Generates and sends briefing to arriving first responders.
    Called by manager with one click.
    """
    from firebase_admin import db as fdb
    crisis_ref = fdb.reference(f"/hotels/{HOTEL_ID}/active_crises/{crisis_id}")
    crisis_data = crisis_ref.get()

    if not crisis_data:
        raise HTTPException(status_code=404, detail="Crisis not found")

    hotel_info = {
        "name": "Hotel Grand",
        "address": "MG Road, Ludhiana, Punjab",
        "floors": 8
    }

    guest_stats = {
        "safe": crisis_data.get("guests_safe", 0),
        "need_help": crisis_data.get("guests_need_help", 0),
        "unknown": crisis_data.get("guests_unknown", 0)
    }

    briefing = generate_responder_briefing(
        crisis_data,
        hotel_info,
        crisis_data.get("staff_assignments", []),
        guest_stats
    )

    result = send_responder_briefing(
        phone=responder_phone,
        briefing=briefing,
        live_link=f"https://aria-crisis.run.app/live/{crisis_id}"
    )

    add_crisis_timeline_event(
        crisis_id,
        f"First responder briefing sent to {service_type}: {responder_phone[-4:]}",
        "MANAGER"
    )

    return {"status": "sent", "service": service_type}
