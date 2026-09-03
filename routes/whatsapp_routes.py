import threading
from flask import Blueprint, request, jsonify

whatsapp_bp = Blueprint('whatsapp', __name__)


def _send_whatsapp_message(phone, message):
    """
    Runs in a background thread. Uses pywhatkit, which drives an actual
    browser window (WhatsApp Web) and simulates the keystrokes needed to
    send the message — including pressing Enter, so no manual click is
    needed once WhatsApp Web is linked on this machine.

    IMPORTANT: This requires:
      1. A real desktop/GUI session (won't work on a headless server).
      2. WhatsApp Web already linked once on this browser (one-time QR scan
         — this is a WhatsApp security requirement that cannot be skipped).
      3. The machine must stay awake/unlocked while this runs, since it
         controls the mouse/keyboard briefly.
    """
    import pywhatkit
    try:
        clean_phone = ''.join(filter(str.isdigit, phone))
        if not clean_phone.startswith('91'):
            clean_phone = '91' + clean_phone
        full_number = '+' + clean_phone

        pywhatkit.sendwhatmsg_instantly(
            phone_no=full_number,
            message=message,
            wait_time=12,
            tab_close=True,
            close_time=3
        )
    except Exception as e:
        print(f"[WhatsApp automation error] {e}")


@whatsapp_bp.route('/api/send-whatsapp', methods=['POST'])
def send_whatsapp():
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '')
    message = data.get('message', '')

    if not phone or not message:
        return jsonify({'error': 'phone and message are required'}), 400

    thread = threading.Thread(target=_send_whatsapp_message, args=(phone, message))
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'sending',
        'note': 'WhatsApp Web will open automatically and the message will send within ~15 seconds — no manual click needed.'
    })