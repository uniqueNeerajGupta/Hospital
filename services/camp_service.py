import json
import os
import uuid
from datetime import datetime

CAMPS_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'camps.json')


def _load():
    if not os.path.exists(CAMPS_PATH):
        return {"camps": []}
    with open(CAMPS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(CAMPS_PATH), exist_ok=True)
    with open(CAMPS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_camp(village, location, date, time, services, asha_name, asha_phone):
    data = _load()
    camp = {
        "id": str(uuid.uuid4())[:8],
        "village": village,
        "location": location,
        "date": date,
        "time": time,
        "services": services,  # list of strings e.g. ["Vaccination", "BP Check", "ANC Checkup"]
        "asha_name": asha_name,
        "asha_phone": asha_phone,
        "created_at": datetime.utcnow().isoformat(),
        "beneficiaries": [],  # list of {name, phone, registered_at, checked_in: bool, checked_in_at}
    }
    data["camps"].append(camp)
    _save(data)
    return camp


def list_camps(village=None):
    data = _load()
    camps = data["camps"]
    if village:
        camps = [c for c in camps if village.lower() in c["village"].lower()]
    # Only show upcoming/today camps first
    camps.sort(key=lambda c: c["date"])
    return camps


def get_camp(camp_id):
    data = _load()
    for c in data["camps"]:
        if c["id"] == camp_id:
            return c
    return None


def register_beneficiary(camp_id, name, phone):
    data = _load()
    for c in data["camps"]:
        if c["id"] == camp_id:
            # avoid duplicate registration by phone
            existing = next((b for b in c["beneficiaries"] if b["phone"] == phone), None)
            if existing:
                return c, existing
            beneficiary = {
                "id": str(uuid.uuid4())[:8],
                "name": name,
                "phone": phone,
                "registered_at": datetime.utcnow().isoformat(),
                "checked_in": False,
                "checked_in_at": None,
            }
            c["beneficiaries"].append(beneficiary)
            _save(data)
            return c, beneficiary
    return None, None


def check_in_beneficiary(camp_id, beneficiary_id):
    data = _load()
    for c in data["camps"]:
        if c["id"] == camp_id:
            for b in c["beneficiaries"]:
                if b["id"] == beneficiary_id:
                    b["checked_in"] = True
                    b["checked_in_at"] = datetime.utcnow().isoformat()
                    _save(data)
                    return b
    return None


def get_missed_beneficiaries(camp_id):
    camp = get_camp(camp_id)
    if not camp:
        return []
    return [b for b in camp["beneficiaries"] if not b["checked_in"]]


def get_attended_beneficiaries(camp_id):
    camp = get_camp(camp_id)
    if not camp:
        return []
    return [b for b in camp["beneficiaries"] if b["checked_in"]]