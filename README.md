<div align="center">

# 🩺 PR Harvest

### AI-Powered Rural Primary Healthcare Triage Platform

**NEXORA 2026 Hackathon** · Problem Statement `PR•HARVEST` · Team Goku
Nirmala Memorial Foundation College

[![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/status-hackathon--prototype-orange)](#)

[Problem](#-the-problem) · [Solution](#-our-solution) · [Features](#-features) · [Tech Stack](#-tech-stack) · [Setup](#-getting-started) · [Roadmap](#-roadmap)

</div>

---

## 📌 The Problem

Over **65% of India's population lives in rural and tier-2 areas**, where access to timely healthcare remains a fundamental challenge:

- 🏥 **70% of the population has no access to specialist care** — 80% of specialists live in urban areas
- 🚑 Nearest hospital is often **hours away**, and the **golden hour** (the critical first 60 minutes in emergencies) is frequently missed
- 🗣️ **Language barriers** make it hard to describe symptoms or understand medical guidance
- 💰 **High out-of-pocket costs** and confusing insurance/referral chains delay treatment
- 📋 **No unified health records** — patients repeat their medical history at every visit
- 😟 Without guidance, people either **ignore serious symptoms** or make **unnecessary long trips** for minor issues

This isn't just an access problem — it's a **decision-making problem**. People don't know whether they need rest, a clinic visit, or emergency care, and by the time they find out, it's often too late.

---

## 💡 Our Solution

**PR Harvest** is an AI-assisted preliminary triage platform that helps rural and tier-2 users quickly understand the urgency of their health situation — in their own language — and guides them to the right next step, without requiring a hospital visit just to find out if one is needed.

> ⚠️ **PR Harvest offers preliminary guidance only and is not a medical diagnosis.** Users are always advised to consult a qualified doctor for serious or worsening symptoms.

---

## ✨ Features

### 🩺 Symptom Triage
Users describe symptoms via text or voice and receive an instant urgency level — **Low, Medium, or High** — with clear next steps (rest at home, visit a clinic, or seek emergency care).

### 🗣️ Multi-Language Support
The entire interface is available in **8 Indian languages**: English, Hindi, Marathi, Bengali, Tamil, Telugu, Gujarati, and Punjabi — so language is never a barrier to understanding your own health.

### 📍 Nearby Hospital Locator
A real, map-based directory of **170+ verified Mumbai hospitals** (names, addresses, coordinates, and contact numbers sourced from Google Maps), filterable by specialty (Cardiology, Oncology, Orthopedics, Maternity, Paediatrics, Ophthalmology).

### 🏥 Admission Assistant
When a doctor advises hospital admission, this feature:
- Detects the user's **live location** and shows nearby hospitals sorted by distance
- Renders an **in-app interactive map** with real driving routes and turn-by-turn directions (powered by OpenStreetMap + OSRM — no paid API keys required)
- Lets the user **reserve a bed** (General Ward / Semi-Private / Private / ICU) in advance, generating a booking confirmation code — reducing paperwork on arrival and giving the hospital advance notice to prepare

### 🚨 Emergency Access
A dedicated, high-visibility **Emergency button** in the navigation bar for one-tap access to urgent care flows.

### 📋 Symptom History *(planned)*
A simple record of past symptom checks so users — and any doctor they later visit — have useful context.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML5, CSS3, Vanilla JS |
| Mapping & Routing | Leaflet.js, OpenStreetMap, OSRM (free, no API key) |
| Data | JSON (hospital directory), SQLAlchemy-ready structure |
| Voice/Language *(planned)* | Bhashini API (Govt. of India, 22-language TTS) |
| Health Records *(planned)* | ABHA / Ayushman Bharat Digital Mission (ABDM) sandbox |

---

## 📁 Project Structure

```
Hospital/
├── app/                        # (or root-level, depending on setup)
│   ├── __init__.py
│   ├── config.py
│   ├── routes/
│   │   ├── main_routes.py      # Home, About, Emergency routes
│   │   ├── triage_routes.py    # Symptom check API
│   │   └── auth_routes.py
│   ├── models/
│   ├── services/
│   │   ├── triage_engine.py    # Rule-based urgency classification
│   │   ├── nlp_processor.py
│   │   └── language_translator.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── data/
│   │       └── mumbai_hospitals_full.json
│   ├── templates/
│   │   ├── index.html          # Landing page
│   │   ├── admission.html      # Admission Assistant (map + booking)
│   │   ├── symptom_form.html
│   │   └── result.html
│   └── utils/
├── data/
├── tests/
├── requirements.txt
├── main.py                     # App entry point
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/uniqueNeerajGupta/Hospital.git
cd Hospital

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install flask flask-sqlalchemy flask-migrate python-dotenv requests
pip freeze > requirements.txt
```

### Run the app

```bash
python main.py
```

Then open **http://127.0.0.1:5000** in your browser.

---

## 🗺️ Roadmap

- [x] AI-assisted symptom triage engine
- [x] 8-language interface
- [x] Real hospital directory with map + live routing
- [x] Bed booking/reservation flow (demo)
- [ ] Emergency SOS with GPS + auto-dispatch (108 integration)
- [ ] Bhashini API integration for real voice guidance
- [ ] ABHA-based digital health pass
- [ ] ASHA/community health worker companion tool
- [ ] Offline-first / low-connectivity mode for rural network conditions

---

## ⚠️ Known Limitations (Honest Disclosure)

We believe in being transparent about what's real vs. simulated in this prototype:

| Feature | Status |
|---|---|
| Hospital names, addresses, coordinates, ratings | ✅ Real (Google Maps verified) |
| Symptom triage logic | ✅ Real (rule-based engine) |
| Live location & routing | ✅ Real (browser geolocation + OSRM) |
| Bed availability & pricing | ⚠️ Simulated for demo — no hospital publicly exposes live bed-inventory APIs |
| Bed booking/reservation | ⚠️ Simulated — not connected to a real hospital admission system |
| Voice guidance | 🔲 Planned — requires Bhashini API integration |
| Digital health pass | 🔲 Planned — requires ABDM/ABHA sandbox integration |

Production deployment of the bed-availability and insurance-approval features would require direct partnerships with hospital HMS providers and integration with India's **National Health Claims Exchange (NHCX)**.

---

## 👥 Team

**Team Goku** · NEXORA 2026 · Team ID: `NXH037`
Nirmala Memorial Foundation College

| Role | Name |
|---|---|
| Team Leader | Neeraj Gupta |

---

## 📄 License

This project was built for the NEXORA 2026 Innovation Hackathon (Department of Information Technology, Vivek College of Commerce). Currently unlicensed for public/commercial use — for demo and educational purposes only.

---

<div align="center">

*Because healthcare shouldn't be a privilege based on geography.*

</div>