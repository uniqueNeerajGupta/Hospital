<div align="center">

# 🩺 PR Harvest

### AI-Powered Rural Primary Healthcare Platform

**NEXORA 2026 Hackathon** · Problem Statement `PR•HARVEST` · Team Goku
Nirmala Memorial Foundation College

[![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/status-hackathon--prototype-orange)](#)

[Problem](#-the-problem) · [Solution](#-our-solution) · [Features](#-features) · [Tech Stack](#-tech-stack) · [Setup](#-getting-started) · [Limitations](#-known-limitations)

</div>

---

## 📌 The Problem

Over **65% of India's population** lives in rural and tier-2 areas, where access to timely healthcare remains a fundamental challenge:

- 🏥 **70% of the population has no access to specialist care** — 80% of specialists live in urban areas
- 🚑 The nearest hospital is often **hours away**, and the **golden hour** (the critical first 60 minutes in emergencies) is frequently missed
- 🗣️ **Language barriers** make it hard to describe symptoms or understand medical guidance
- 💰 **70% of health spending is out-of-pocket** — many families don't know they're eligible for free government treatment
- 📋 **No unified health records** — patients repeat their medical history at every visit
- 😟 Without guidance, people either **ignore serious symptoms** or make **unnecessary long trips** for minor issues
- 📢 **Awareness gaps** — government health drives (like Pulse Polio) already exist, but many families never hear about them in time

This isn't just an access problem — it's a **decision-making and awareness problem**.

---

## 💡 Our Solution

**PR Harvest** is an AI-assisted healthcare platform that covers the *entire* journey a rural family takes when someone falls sick — from the first symptom, to emergency response, to a booked hospital bed, to knowing what government support they qualify for.

> ⚠️ **PR Harvest offers preliminary guidance only and is not a medical diagnosis.** Users are always advised to consult a qualified doctor for serious or worsening symptoms.

---

## ✨ Features

### 🩺 Symptom Triage
Text or voice input, instant urgency level — **Low, Medium, or High** — with clear next steps (rest at home, visit a clinic, or seek emergency care). Works in **8 Indian languages**. Includes an **offline mode** (PWA + Service Worker) that keeps working without internet, using an on-device copy of the triage logic.

### 🤖 AI Health Assistant (Chatbot)
A conversational chatbot (GPT-4o-mini) that asks clarifying questions one at a time, accepts photo uploads (X-rays, blood reports, prescriptions), and supports **voice input/output**. It reads doctor-written prescriptions and offers to auto-fill a medicine reminder roadmap — but never prescribes medicine or diagnoses a disease itself, and never claims to authenticate whether a medicine is genuine from a photo (by design — false confidence there could cause real harm).

### 🚨 One-Tap Emergency SOS
A floating SOS button, always accessible. One tap starts a visible countdown; if not cancelled, it automatically sends the user's **live location via WhatsApp** to a saved emergency contact and opens the phone dialer to call for help — designed for minimal interaction during a real emergency.

### 🏥 Admission Assistant
A live map (OpenStreetMap/Leaflet — no Google Maps dependency) of **170+ real, verified Mumbai hospitals**, filterable by specialty. Shows real driving routes and turn-by-turn directions calculated in-app (OSRM), and lets users **reserve a hospital bed** using a saved patient profile — with an automatic WhatsApp booking confirmation sent to family.

### 🤖 Autonomous Booking Agent
A conversational agent (OpenAI function calling) that can **search hospitals and complete a bed booking on its own** — e.g., "my father has chest pain, get him a bed" — picking the best hospital by distance, rating, and availability, and showing a live action log of what it did.

### 🎙️ Persistent Voice Agent
A site-wide, always-listening voice assistant (toggle on/off with a status light) that understands natural spoken requests — even vague ones — and can navigate to the right feature or trigger a real booking, explaining what it's doing as it goes. Built on the Web Speech API plus the same AI agent backend.

### 💰 Government Schemes Checker
A 4-question eligibility checker for **Ayushman Bharat (PM-JAY)** — up to ₹5 lakh/year in free hospital treatment — plus informational cards on PM Jan Aushadhi (cheap generic medicines), PM Matru Vandana Yojana, Janani Suraksha Yojana, and low-cost government insurance schemes (PMSBY, PMJJBY). All figures are based on real, published scheme criteria.

### 💉 Government Health Camps Awareness
An awareness board explaining recurring national health programs (Pulse Polio, Mission Indradhanush, National Deworming Day, Ayushman Bharat screening camps) with a **WhatsApp alert subscription** so users are notified when one is confirmed near their village.

### 🗣️ Multi-Language Support
The entire interface is available in **8 Indian languages**: English, Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, and Punjabi — with the chosen language persisting across every page.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, Vanilla JS |
| AI / Chat / Agent | OpenAI (GPT-4o-mini), function calling |
| Voice | Web Speech API (speech-to-text + text-to-speech) |
| Mapping & Routing | Leaflet.js, OpenStreetMap, OSRM (free, no API key) |
| Messaging Automation | `pywhatkit` (WhatsApp Web automation) |
| Data | JSON-based storage (hospital directory, camp/awareness records) |
| Offline Support | Service Worker, Web App Manifest (PWA) |

---

## 📁 Project Structure

```
healthcare/
├── main.py                     # App entry point — all routes + blueprints
├── routes/
│   ├── chat_routes.py          # AI chatbot (/api/chat)
│   ├── whatsapp_routes.py      # WhatsApp automation (/api/send-whatsapp)
│   ├── agent_routes.py         # Autonomous booking agent (/api/agent)
│   └── awareness_routes.py     # Govt. health camp alert subscriptions
├── services/
│   ├── hospital_service.py     # Hospital search + booking logic
│   └── awareness_service.py    # Subscriber storage
├── static/
│   ├── js/
│   │   ├── offline-triage.js   # On-device triage engine (offline mode)
│   │   ├── site-language.js    # Cross-page language persistence
│   │   ├── sos-widget.js       # One-tap emergency SOS widget
│   │   ├── voice-agent.js      # Persistent voice assistant
│   │   └── sw.js               # Service worker (PWA offline support)
│   ├── manifest.json
│   └── data/
│       └── mumbai_hospitals_full.json
└── templates/
    ├── index.html                    # Homepage
    ├── triage.html                   # Symptom checker
    ├── emg.html                      # Emergency SOS
    ├── admission.html                # Hospital finder + booking
    ├── chatbot.html                  # AI health assistant chat
    ├── agent.html                    # Autonomous booking agent
    ├── scheme-checker.html           # Government schemes
    ├── government-activities.html    # Health camp awareness
    └── about.html                    # About PR Harvest
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip
- An OpenAI API key (for chatbot/agent/voice features)

### Installation

```bash
git clone https://github.com/uniqueNeerajGupta/Hospital.git
cd Hospital

python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

pip install flask python-dotenv openai pywhatkit pyautogui
```

Create a `.env` file:
```
OPENAI_API_KEY=sk-...
```

### Run the app

```bash
python main.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## ⚠️ Known Limitations (Honest Disclosure)

We believe in being transparent about what's real vs. simulated in this prototype:

| Feature | Status |
|---|---|
| Hospital names, addresses, coordinates, ratings | ✅ Real (Google Maps verified) |
| Map routing & directions | ✅ Real (OSRM routing engine) |
| Government scheme eligibility criteria | ✅ Real, verified against official sources |
| Symptom triage logic | ✅ Real (rule-based + AI) |
| Live location & emergency WhatsApp/call | ✅ Real (browser geolocation + WhatsApp automation) |
| Bed availability & pricing | ⚠️ Simulated for demo — no hospital publicly exposes live bed-inventory APIs |
| Bed booking/reservation | ⚠️ Simulated — not connected to a real hospital admission system |
| WhatsApp automation | ⚠️ Uses browser automation (`pywhatkit`) for the demo — production would need the Meta WhatsApp Business API |
| Medicine authenticity detection | ❌ Deliberately not implemented — an AI photo-based "fake medicine" verdict could be wrong and dangerous; the app instead guides users to real verification methods |

Production deployment of bed-availability, insurance-approval, and WhatsApp-at-scale features would require direct partnerships with hospital HMS providers, India's **National Health Claims Exchange (NHCX)**, and Meta's WhatsApp Business API.

---

## 👥 Team

**Team Goku** · NEXORA 2026 · Team ID: `NXH037`
Nirmala Memorial Foundation College

| Role | Name |
|---|---|
| Team Leader | Neeraj Gupta |
| Contact | [+91 99870 03075](tel:+919987003075) |

---

## 📄 License

This project was built for the NEXORA 2026 Innovation Hackathon (Department of Information Technology, Vivek College of Commerce). Currently unlicensed for public/commercial use — for demo and educational purposes only.

---

<div align="center">

*Because healthcare shouldn't be a privilege based on geography.*

</div>