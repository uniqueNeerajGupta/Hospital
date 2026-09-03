import threading
from flask import Blueprint, request, jsonify
from services.awareness_service import subscribe

awareness_bp = Blueprint('awareness', __name__)


@awareness_bp.route('/api/awareness/subscribe', methods=['POST'])
def api_subscribe():
    data = request.get_json(silent=True) or {}
    program = data.get('program', '').strip()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    village = data.get('village', '').strip()

    if not all([program, name, phone, village]):
        return jsonify({'error': 'program, name, phone, and village are all required'}), 400

    sub = subscribe(program, name, phone, village)

    # Send an immediate WhatsApp confirmation so the person knows it worked
    message = (
        f"🔔 Shivir Sandesh — Alert Set\n\n"
        f"Hi {name}, you'll now be notified by WhatsApp whenever a \"{program}\" camp or drive "
        f"is announced near {village}.\n\n"
        f"No action needed now — we'll message you when it's confirmed."
    )
    _send_whatsapp_async(phone, message)

    return jsonify({'subscriber': sub})


def _send_whatsapp_async(phone, message):
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
            print(f"[Awareness WhatsApp error] {e}")

    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()