import threading
from flask import Blueprint, request, jsonify

from services.camp_service import (
    create_camp, list_camps, get_camp, register_beneficiary,
    check_in_beneficiary, get_missed_beneficiaries, get_attended_beneficiaries
)

camp_bp = Blueprint('camp', __name__)


@camp_bp.route('/api/camps', methods=['GET'])
def api_list_camps():
    village = request.args.get('village')
    camps = list_camps(village)
    # Don't leak full beneficiary list publicly — just counts
    public_camps = []
    for c in camps:
        public_camps.append({
            **{k: v for k, v in c.items() if k != 'beneficiaries'},
            'registered_count': len(c['beneficiaries']),
            'checked_in_count': sum(1 for b in c['beneficiaries'] if b['checked_in']),
        })
    return jsonify({'camps': public_camps})


@camp_bp.route('/api/camps', methods=['POST'])
def api_create_camp():
    data = request.get_json(silent=True) or {}
    required = ['village', 'location', 'date', 'time', 'services', 'asha_name', 'asha_phone']
    if not all(data.get(f) for f in required):
        return jsonify({'error': 'Missing required camp details'}), 400

    camp = create_camp(
        village=data['village'], location=data['location'], date=data['date'],
        time=data['time'], services=data['services'],
        asha_name=data['asha_name'], asha_phone=data['asha_phone']
    )
    return jsonify({'camp': camp})


@camp_bp.route('/api/camps/<camp_id>', methods=['GET'])
def api_get_camp(camp_id):
    camp = get_camp(camp_id)
    if not camp:
        return jsonify({'error': 'Camp not found'}), 404
    return jsonify({'camp': camp})


@camp_bp.route('/api/camps/<camp_id>/register', methods=['POST'])
def api_register_beneficiary(camp_id):
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    if not name or not phone:
        return jsonify({'error': 'name and phone are required'}), 400

    camp, beneficiary = register_beneficiary(camp_id, name, phone)
    if not camp:
        return jsonify({'error': 'Camp not found'}), 404

    # Fire-and-forget WhatsApp confirmation with camp details (multi-channel notification)
    message = (
        f"🏕️ Shivir Sandesh — Health Camp Confirmed\n\n"
        f"Hi {name}, you're registered for the health camp at {camp['location']}, {camp['village']}.\n\n"
        f"📅 Date: {camp['date']}\n"
        f"🕐 Time: {camp['time']}\n"
        f"🩺 Services: {', '.join(camp['services'])}\n\n"
        f"Show this message or your name at the camp to check in. See you there!"
    )
    _send_whatsapp_async(phone, message)

    return jsonify({'camp_id': camp_id, 'beneficiary': beneficiary})


@camp_bp.route('/api/camps/<camp_id>/checkin', methods=['POST'])
def api_checkin(camp_id):
    data = request.get_json(silent=True) or {}
    beneficiary_id = data.get('beneficiary_id')
    if not beneficiary_id:
        return jsonify({'error': 'beneficiary_id is required'}), 400

    beneficiary = check_in_beneficiary(camp_id, beneficiary_id)
    if not beneficiary:
        return jsonify({'error': 'Beneficiary or camp not found'}), 404

    return jsonify({'beneficiary': beneficiary})


@camp_bp.route('/api/camps/<camp_id>/attendance', methods=['GET'])
def api_attendance(camp_id):
    camp = get_camp(camp_id)
    if not camp:
        return jsonify({'error': 'Camp not found'}), 404
    return jsonify({
        'attended': get_attended_beneficiaries(camp_id),
        'missed': get_missed_beneficiaries(camp_id),
    })


@camp_bp.route('/api/camps/<camp_id>/followup', methods=['POST'])
def api_followup(camp_id):
    camp = get_camp(camp_id)
    if not camp:
        return jsonify({'error': 'Camp not found'}), 404

    missed = get_missed_beneficiaries(camp_id)
    if not missed:
        return jsonify({'status': 'no_missed', 'count': 0})

    for b in missed:
        message = (
            f"🏕️ Shivir Sandesh — We Missed You\n\n"
            f"Hi {b['name']}, you were registered for the health camp at {camp['location']}, {camp['village']} "
            f"but we didn't see you there. Services offered: {', '.join(camp['services'])}.\n\n"
            f"Please visit your nearest PHC, or watch for the next camp announcement. Your health matters!"
        )
        _send_whatsapp_async(b['phone'], message)

    return jsonify({'status': 'sending', 'count': len(missed)})


def _send_whatsapp_async(phone, message):
    """Reuses the same pywhatkit automation as the rest of the site."""
    def _send():
        try:
            import pywhatkit
            clean_phone = ''.join(filter(str.isdigit, phone))
            if not clean_phone.startswith('91'):
                clean_phone = '91' + clean_phone
            pywhatkit.sendwhatmsg_instantly(
                phone_no='+' + clean_phone, message=message,
                wait_time=12, tab_close=True, close_time=3
            )
        except Exception as e:
            print(f"[Camp WhatsApp error] {e}")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()