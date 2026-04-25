# 🚨 ARIA — Adaptive Response Intelligence for Hospitality

> **AI-powered emergency coordination system for hospitality venues**
> Built by **THE_PHOENIX** | Google Solution Challenge 2026

[![Live Demo](https://img.shields.io/badge/Live-Demo-green)](https://aria-crisis.run.app)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Google-Gemini_1.5_Pro-4285F4)](https://deepmind.google/technologies/gemini)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB-FFCA28)](https://firebase.google.com)

---

## 🎯 Problem

Hotels and hospitality venues have **no intelligent coordination system** during emergencies:
- Staff communicate via chaotic radio with no structure
- Guests receive no information and panic
- Emergency services arrive blind with no building context
- Same mistakes repeat — no learning system exists
- Language barriers leave international guests uninformed

**Every second of delay in emergency response increases risk by 40%.**

---

## 💡 Solution — ARIA

ARIA is a **multi-agent AI system** that classifies crises in under **3 seconds**, coordinates the entire response, and learns from every incident.

```
Guest/Staff Reports Emergency
           ↓
Gemini 1.5 Pro Classifies (3 sec)
           ↓
Staff Assigned with Specific Tasks (5 sec)
           ↓
Guests Alerted in Their Language (10 sec)
           ↓
Manager Gets Full Command View
           ↓
First Responders Get Live Briefing
           ↓
Crisis Resolved → AI Learning Report
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     ARIA SYSTEM                         │
├──────────────┬──────────────────┬───────────────────────┤
│   SENSE      │     DECIDE       │       LEARN           │
│              │                  │                       │
│ Crisis       │ Gemini 1.5 Pro   │ Vertex AI             │
│ Detection    │ Role Assignment  │ Post-crisis           │
│ & Input      │ Multi-crisis     │ Analysis              │
│              │ Orchestration    │                       │
└──────┬───────┴────────┬─────────┴───────────┬───────────┘
       │                │                     │
       ▼                ▼                     ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐
│  Firebase   │  │  FastAPI    │  │   Three Portals     │
│  Realtime   │◄─┤  Backend   ├─►│  Manager | Staff    │
│  Database   │  │            │  │  Guest              │
└─────────────┘  └─────┬───────┘  └─────────────────────┘
                       │
              ┌────────┴────────┐
              │   Integrations  │
              │                 │
              │ Twilio SMS/WA   │
              │ Google Translate│
              │ Google Maps     │
              └─────────────────┘
```

---

## 👥 Three Portals

| Portal | Access | Capabilities |
|--------|--------|-------------|
| 🔴 **Command** | Manager | Full crisis view, staff control, emergency contacts, learning reports |
| 🟡 **Responder** | Staff/Security/Nurse | Own task only, status updates, incident reporting |
| 🟢 **Guest** | Hotel guests | Multilingual alerts, safe/help response, emergency report |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI Brain | Google Gemini 1.5 Pro |
| Backend | FastAPI (Python) |
| Database | Firebase Realtime Database |
| Auth | Firebase Authentication |
| SMS/WhatsApp | Twilio |
| Translation | Google Translate API |
| Maps | Google Maps Platform |
| Deployment | Google Cloud Run |
| Post-crisis ML | Vertex AI |
| Voice Input | Google Speech-to-Text |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud account with Gemini API enabled
- Firebase project with Realtime Database
- Twilio account (free trial works)

### 1. Clone the repository
```bash
git clone https://github.com/THE-PHOENIX/ARIA.git
cd ARIA
```

### 2. Set up backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### 3. Configure Firebase
- Go to Firebase Console → Project Settings → Service Accounts
- Download `serviceAccountKey.json`
- Place it in the `backend/` folder

### 4. Load demo data
```bash
python firebase_client.py
```

### 5. Test the AI brain
```bash
python gemini_engine.py
```

### 6. Start the server
```bash
uvicorn main:app --reload --port 8000
```

### 7. Open the API docs
```
http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/crisis/report` | Report emergency — triggers full ARIA response |
| `GET` | `/crisis/active` | Get all active crises |
| `POST` | `/crisis/close` | Resolve crisis + generate learning report |
| `GET` | `/staff/all` | Get all staff and their status |
| `POST` | `/staff/location` | Staff checks in from location |
| `POST` | `/staff/task-status` | Update task progress |
| `POST` | `/guest/register` | Register guest at check-in |
| `POST` | `/guest/safety-response` | Guest marks safe or needs help |
| `POST` | `/responder/brief/{id}` | Send briefing to fire brigade/ambulance |

---

## 🎬 Demo Script

For judges — here's exactly what to trigger:

```bash
# 1. Register a demo guest
POST /guest/register
{
  "room": "room_412",
  "name": "Demo Guest",
  "phone": "+91XXXXXXXXXX",
  "language": "hi",
  "floor": 4
}

# 2. Trigger a crisis (watch SMS arrive in real time)
POST /crisis/report
{
  "report": "Fire and smoke in kitchen, Floor 2, guests panicking",
  "reported_by": "staff_001",
  "reporter_location": "Floor 2"
}

# 3. Watch Firebase dashboard update live
# 4. Check SMS on demo phones
# 5. Close crisis and see learning report
POST /crisis/close
{
  "crisis_id": "<id from step 2>",
  "resolved_by": "staff_003"
}
```

---

## 👨‍💻 Team THE_PHOENIX

| Name | Role |
|------|------|
| **Prikshit** | AI Backend, Gemini Engine, Firebase, System Architecture |
| **Mohit** | Frontend Portals, Integration, Deployment |

---

## 📄 License

MIT License — built for Google Solution Challenge 2026
