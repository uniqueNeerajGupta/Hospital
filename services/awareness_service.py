import json
import os
import uuid
from datetime import datetime

SUBSCRIBERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'awareness_subscribers.json')


def _load():
    if not os.path.exists(SUBSCRIBERS_PATH):
        return {"subscribers": []}
    with open(SUBSCRIBERS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(SUBSCRIBERS_PATH), exist_ok=True)
    with open(SUBSCRIBERS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def subscribe(program, name, phone, village):
    data = _load()
    # avoid duplicate subscription to the same program by the same phone
    existing = next((s for s in data["subscribers"] if s["phone"] == phone and s["program"] == program), None)
    if existing:
        return existing

    sub = {
        "id": str(uuid.uuid4())[:8],
        "program": program,
        "name": name,
        "phone": phone,
        "village": village,
        "subscribed_at": datetime.utcnow().isoformat(),
    }
    data["subscribers"].append(sub)
    _save(data)
    return sub


def get_subscribers(program=None, village=None):
    data = _load()
    subs = data["subscribers"]
    if program:
        subs = [s for s in subs if s["program"] == program]
    if village:
        subs = [s for s in subs if village.lower() in s["village"].lower()]
    return subs