"""
alert_sender.py
───────────────
Handles all outgoing alerts from ARIA.
- SMS via Twilio (works on any phone, no app needed)
- WhatsApp via Twilio (if guest registered with WhatsApp)
"""

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# ── Twilio Setup ──────────────────────────────────────────────────────────────
client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


# ══════════════════════════════════════════════════════════════════════════════
# SEND SMS
# ══════════════════════════════════════════════════════════════════════════════

def send_sms(to_number: str, message: str) -> dict:
    """
    Sends an SMS to a phone number.
    Returns status dict with success/failure info.
    """
    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=to_number
        )
        print(f"  ✅ SMS sent to {to_number} | SID: {msg.sid}")
        return {"success": True, "sid": msg.sid, "to": to_number}

    except Exception as e:
        print(f"  ❌ SMS failed to {to_number} | Error: {str(e)}")
        return {"success": False, "error": str(e), "to": to_number}


# ══════════════════════════════════════════════════════════════════════════════
# SEND WHATSAPP
# ══════════════════════════════════════════════════════════════════════════════

def send_whatsapp(to_number: str, message: str) -> dict:
    """
    Sends a WhatsApp message via Twilio Sandbox.
    Note: For production, you need WhatsApp Business API approval.
    For demo/hackathon, Twilio sandbox works perfectly.
    """
    try:
        msg = client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_NUMBER}",
            to=f"whatsapp:{to_number}"
        )
        print(f"  ✅ WhatsApp sent to {to_number} | SID: {msg.sid}")
        return {"success": True, "sid": msg.sid, "to": to_number}

    except Exception as e:
        print(f"  ❌ WhatsApp failed to {to_number} | Error: {str(e)}")
        return {"success": False, "error": str(e), "to": to_number}


# ══════════════════════════════════════════════════════════════════════════════
# BULK GUEST ALERTS
# ══════════════════════════════════════════════════════════════════════════════

def send_bulk_guest_alerts(guests: list, alert_messages: dict) -> dict:
    """
    Sends alerts to all affected guests.

    guests: list of guest objects from Firebase
    alert_messages: dict of {room: message_text} from Gemini

    Returns summary of sent/failed alerts.
    """
    results = {"sent": 0, "failed": 0, "details": []}

    for guest in guests:
        room = guest.get("room")
        phone = guest.get("phone")
        message = alert_messages.get(room)

        if not phone or not message:
            continue

        # Try SMS first (works on any phone)
        result = send_sms(phone, message)

        if result["success"]:
            results["sent"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "room": room,
            "phone": phone[-4:],    # Only log last 4 digits for privacy
            "status": "sent" if result["success"] else "failed"
        })

    return results


# ══════════════════════════════════════════════════════════════════════════════
# STAFF TASK ALERTS
# ══════════════════════════════════════════════════════════════════════════════

def send_staff_alert(phone: str, name: str, task: str,
                      crisis_type: str, priority: str) -> dict:
    """
    Sends a task assignment alert to a staff member.
    Short, clear, designed for someone who might be panicking.
    """
    emoji = "🔴" if priority == "URGENT" else "🟡"

    message = (
        f"{emoji} ARIA ALERT — {crisis_type}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Hi {name}, your task:\n\n"
        f"{task}\n\n"
        f"Open ARIA app to confirm. Stay calm. Follow ARIA."
    )

    return send_sms(phone, message)


# ══════════════════════════════════════════════════════════════════════════════
# FIRST RESPONDER BRIEFING SMS
# ══════════════════════════════════════════════════════════════════════════════

def send_responder_briefing(phone: str, briefing: str,
                             live_link: str = None) -> dict:
    """
    Sends a briefing to fire brigade / ambulance / police.
    Includes a live dashboard link if available.
    """
    message = briefing

    if live_link:
        message += f"\n\nLive dashboard: {live_link}"

    # Twilio SMS has 1600 char limit — truncate if needed
    if len(message) > 1550:
        message = message[:1550] + "...\n[See live link for full details]"

    return send_sms(phone, message)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER SUMMARY ALERT
# ══════════════════════════════════════════════════════════════════════════════

def send_manager_alert(phone: str, crisis_type: str,
                        severity: str, location: str,
                        staff_count: int, guest_count: int) -> dict:
    """
    Sends immediate alert to manager when crisis is declared.
    They then open the dashboard for full control.
    """
    message = (
        f"🚨 ARIA CRISIS ALERT\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Type: {crisis_type}\n"
        f"Severity: {severity}\n"
        f"Location: {location}\n"
        f"Staff Dispatched: {staff_count}\n"
        f"Guests Alerted: {guest_count}\n\n"
        f"Open ARIA Command Center now.\n"
        f"ARIA is coordinating. Stay calm."
    )

    return send_sms(phone, message)
