import os
import json
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

from services.hospital_service import search_hospitals, book_bed

load_dotenv()

agent_bp = Blueprint('agent', __name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = """You are the "PR Harvest AI Agent" — a voice-and-text assistant for a rural healthcare website. You do TWO kinds of things:

A) NAVIGATE the user to the right feature on the site, even if they don't remember its exact name — infer the best match from what they describe.
B) ACTUALLY BOOK a hospital bed for them when asked, using real tools — not just talk about it.

THE SITE'S FEATURES (use these when deciding where to send the user):
- page "home" (/) — the main landing page with an overview of everything.
- page "triage" (/triage) — describe symptoms (typed or spoken) and get an instant urgency level: rest at home, visit a clinic, or seek emergency care.
- page "emergency" (/emg) — one-tap SOS: alerts family via WhatsApp with live location and can call for help immediately. For anything urgent/dangerous, send them here.
- page "find_hospital" (/find-clinic) — a live map of nearby hospitals with real distances, directions, and the ability to book a bed with a saved profile.
- page "scheme_checker" (/scheme-checker) — checks eligibility for free government healthcare schemes like Ayushman Bharat (PM-JAY), which can cover up to ₹5 lakh in free treatment.
- page "chat" (/chat) — a text/voice chatbot for back-and-forth symptom questions and general health guidance.
- page "agent" (/agent) — this same booking agent, as a dedicated page.

HOW TO DECIDE WHAT THE USER WANTS:
- Users often don't remember exact feature names. Infer intent from vague or partial descriptions — e.g. "mujhe pata nahi hai kya karu, bukhar hai" → triage. "paisa nahi hai ilaj ke liye" → scheme_checker. "mujhe abhi turant kisi ko batana hai" → emergency. "mujhe hospital mein bed chahiye" → either navigate to find_hospital OR directly search/book using your tools if they've given enough detail (symptom/reason + you have their profile).
- If the user's intent is genuinely unclear even after reasonable inference, ask ONE short clarifying question instead of guessing wrong.

WHEN YOU CALL navigate_to:
- Also briefly explain (1-2 short sentences) what that page does, so the user understands what they're about to see even before it loads — this matters especially for voice, since they'll hear your answer before/as the page opens.

WHEN YOU BOOK A BED (search_hospitals / book_bed):
- Actually complete the booking using the tools — don't just describe how to do it. Use the patient_profile given to you in context; don't ask the user to repeat their name/phone if it's already there.
- Pick the best hospital yourself (closest + highest rated + has an available matching bed) unless results are ambiguous.
- If a booking fails (no beds), automatically try the next best hospital (up to 2 more attempts) before telling the user it didn't work.

IF THE USER ASKS WHAT YOU CAN DO:
- List a few of the site's features in plain language (2-4 sentences), not exhaustively — mention symptom checking, emergency SOS, finding/booking a hospital, and free treatment scheme checking.

RULES:
- NEVER prescribe medicine or diagnose a specific disease — that's not your job here.
- NEVER invent hospital names, distances, or bed availability — only use what tools return.
- Keep spoken replies SHORT (2-4 sentences) — this is often read aloud by text-to-speech.
- Respond in the SAME language the user used (English, Hindi, or Marathi) — match their language exactly, especially for Hindi, since many users will speak Hindi.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "Send the user to a specific page/feature on the site. Infer the best match even if the user didn't name it exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "enum": ["home", "triage", "emergency", "find_hospital", "scheme_checker", "chat", "agent"]
                    }
                },
                "required": ["page"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hospitals",
            "description": "Search for hospitals, optionally filtered by medical specialty, sorted by distance from the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "specialty": {
                        "type": "string",
                        "description": "Medical specialty to filter by, e.g. Cardiology, Pediatrics, Orthopedics, Maternity, Oncology, Ophthalmology. Omit to search all."
                    },
                    "max_results": {"type": "integer", "description": "Max hospitals to return, default 5."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_bed",
            "description": "Reserve a specific bed type at a specific hospital for the patient. Only call this after search_hospitals has confirmed the hospital and bed type exist and are available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hospital_id": {"type": "integer", "description": "The id field of the hospital from search_hospitals results."},
                    "bed_type": {"type": "string", "description": "e.g. General Ward, Semi-Private Room, Private Room, ICU"},
                    "patient_name": {"type": "string"},
                    "patient_phone": {"type": "string"},
                    "reason": {"type": "string", "description": "Short reason for admission, e.g. 'Chest pain', 'Fever', 'Accident injury'"}
                },
                "required": ["hospital_id", "bed_type", "patient_name", "patient_phone", "reason"]
            }
        }
    }
]

PAGE_ROUTES = {
    "home": "/",
    "triage": "/triage",
    "emergency": "/emg",
    "find_hospital": "/find-clinic",
    "scheme_checker": "/scheme-checker",
    "chat": "/chat",
    "agent": "/agent",
}


def execute_tool(name, args, user_lat, user_lng):
    if name == 'navigate_to':
        page = args.get('page', 'home')
        route = PAGE_ROUTES.get(page, '/')
        return {'navigated': True, 'page': page, 'route': route}

    if name == 'search_hospitals':
        results = search_hospitals(
            specialty=args.get('specialty'),
            user_lat=user_lat,
            user_lng=user_lng,
            max_results=args.get('max_results', 5)
        )
        return {'hospitals': results}

    if name == 'book_bed':
        result = book_bed(
            hospital_id=args.get('hospital_id'),
            bed_type=args.get('bed_type'),
            patient_name=args.get('patient_name'),
            patient_phone=args.get('patient_phone'),
            reason=args.get('reason'),
        )
        return result

    return {'error': f'Unknown tool: {name}'}


@agent_bp.route('/api/agent', methods=['POST'])
def run_agent():
    """
    Accepts JSON:
      - message: user's request in natural language
      - history: prior [{role, content}] turns (optional)
      - profile: {name, phone, ...} the user's saved patient profile
      - lat, lng: user's current location (optional but improves results)
    Returns:
      - reply: final natural-language summary from the agent
      - actions: list of tool calls the agent made, for showing a live action log in the UI
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    history = data.get('history', [])
    profile = data.get('profile', {})
    user_lat = data.get('lat')
    user_lng = data.get('lng')

    if not message:
        return jsonify({'error': 'message is required'}), 400

    profile_context = f"\n\n[Patient profile on file: {json.dumps(profile)}]" if profile else ""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message + profile_context})

    actions_log = []
    navigate_route = None
    max_iterations = 6

    try:
        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return jsonify({'reply': msg.content, 'actions': actions_log, 'route': navigate_route})

            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
            })

            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except Exception:
                    fn_args = {}

                result = execute_tool(fn_name, fn_args, user_lat, user_lng)
                actions_log.append({'tool': fn_name, 'args': fn_args, 'result': result})

                if fn_name == 'navigate_to' and result.get('route'):
                    navigate_route = result['route']

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result)
                })

        return jsonify({'reply': "I took several steps but couldn't finish — please check the Admission Assistant to complete this manually.", 'actions': actions_log, 'route': navigate_route})

    except Exception as e:
        return jsonify({'error': f'Agent unavailable right now: {str(e)}', 'actions': actions_log}), 500