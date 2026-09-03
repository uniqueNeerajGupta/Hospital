import json
import math
import os
import random
import string

HOSPITALS_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'data', 'mumbai_hospitals_full.json')

_hospitals_cache = None


def _load_hospitals():
    global _hospitals_cache
    if _hospitals_cache is None:
        with open(HOSPITALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _hospitals_cache = data['hospitals']
    return _hospitals_cache


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def search_hospitals(specialty=None, user_lat=None, user_lng=None, max_results=5):
    """
    Tool: find hospitals, optionally filtered by specialty, sorted by distance
    from the user's location if provided.
    """
    hospitals = _load_hospitals()
    results = list(hospitals)

    if specialty:
        specialty_lower = specialty.lower()
        results = [h for h in results if specialty_lower in h.get('specialty', '').lower()]
        if not results:
            results = list(hospitals)  # fall back to all if no exact specialty match

    if user_lat is not None and user_lng is not None:
        for h in results:
            h_copy_dist = _haversine_km(user_lat, user_lng, h['latitude'], h['longitude'])
            h['_distance_km'] = round(h_copy_dist, 1)
        results.sort(key=lambda h: h['_distance_km'])
    else:
        results.sort(key=lambda h: -h.get('rating', 0))

    trimmed = results[:max_results]
    return [
        {
            'id': h['id'],
            'name': h['name'],
            'specialty': h['specialty'],
            'distance_km': h.get('_distance_km'),
            'rating': h.get('rating'),
            'beds_available': h.get('beds_available'),
            'phone': h.get('phone'),
            'address': h.get('address'),
            'bed_categories': h.get('bed_categories', []),
        }
        for h in trimmed
    ]


def get_hospital_by_id(hospital_id):
    hospitals = _load_hospitals()
    for h in hospitals:
        if h['id'] == hospital_id:
            return h
    return None


def book_bed(hospital_id, bed_type, patient_name, patient_phone, reason):
    """
    Tool: reserve a bed. This mutates the in-memory hospital list for the
    lifetime of the server process (demo persistence) and returns a
    confirmation code, mirroring the logic in the Admission Assistant.
    """
    hospital = get_hospital_by_id(hospital_id)
    if not hospital:
        return {'success': False, 'error': 'Hospital not found'}

    bed_cats = hospital.get('bed_categories', [])
    matched = next((b for b in bed_cats if b['type'].lower() == bed_type.lower()), None)
    if not matched:
        return {'success': False, 'error': f'Bed type "{bed_type}" not found at this hospital. Available: {[b["type"] for b in bed_cats]}'}

    if matched['available'] <= 0:
        return {'success': False, 'error': f'No {bed_type} beds currently available at {hospital["name"]}.'}

    matched['available'] -= 1
    hospital['beds_available'] = max(0, hospital.get('beds_available', 1) - 1)

    code = 'PRH-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    return {
        'success': True,
        'confirmation_code': code,
        'hospital_name': hospital['name'],
        'hospital_phone': hospital.get('phone'),
        'hospital_address': hospital.get('address'),
        'bed_type': matched['type'],
        'price_per_day_inr': matched.get('price_per_day_inr'),
        'patient_name': patient_name,
        'reason': reason,
    }