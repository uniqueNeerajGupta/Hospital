"""
KrishiSeva AI — Agent Backend (Navigation + Proactive Advisory Automation)
============================================================================
Is version me original navigation features ke sath ye naye AI agent
features add kiye gaye hain:

  1. Crop Advisory Agent        -> weather + NDVI dekh ke proactive salah
  2. Expense/Income Tracker     -> voice se kharcha/kamai record + summary
  3. Loan/Scheme Eligibility    -> farm history dekh ke personalized suggestion
  4. Pest/Disease Alert Agent   -> nearby farms ke reports se proactive warning
  5. Price Prediction/Selling   -> "abhi bechu ya ruko" advisory
  6. WhatsApp/SMS Fallback      -> same agent WhatsApp Business API se
  7. Community Q&A (RAG)        -> purane solved farmer problems se jawab
  8. Onboarding Agent           -> conversation se naya farmer profile banaye

NOTE FOR DEV: Is file me kuch jagah `# TODO(you)` comments hain jahan
aapko apne existing models/services ke actual import path daalne honge —
maine placeholder/stub functions rakhe hain jahan actual DB schema
maloom nahi tha, taaki file bina crash kiye chal sake aur aap easily
wire kar sako.

CHANGE LOG:
  - Dashboard navigation fix: login abhi implement nahi hai, isliye
    session me farm_id set nahi hota. Ab "dashboard" bolne par seedha
    default farm_id=14 (/dashboard/14) pe navigate hota hai, /map pe
    fallback hone ki jagah.
============================================================================
"""

import os
import json
import logging
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, session
from functools import wraps
from openai import OpenAI, APIError, APITimeoutError

# TODO(you): apna existing service import barkarar rakho
from services.nearby_mandi import find_nearby_mandis

load_dotenv()

logger = logging.getLogger("krishiseva.agent")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS_FINAL = 300

agent_bp = Blueprint("agent", __name__)


# ---------------------------------------------------------
# AUTH DECORATOR (Critical fix #4 from pehle ki review)
# ---------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------
# ROUTE MAP — panel_name se real Flask route tak
# ---------------------------------------------------------
STATIC_ROUTES = {
    "mandi_price": "/mandi",
    "disease_detection": "/crop-disease",
    "schemes": "/government_schemes",
    "marketplace": "/marketplace",
    "weather": "/weather",
    "farm_map": "/map",
    "expenses": "/expenses",
    "community": "/community",
    "dashboard": "/dashboard/14",
}

# Login abhi nahi hai, isliye session me farm_id set nahi hota.
# Tab tak dashboard ke liye ye default farm_id use hoga.
# TODO(you): jab proper user/farm mapping ho jaye, isse hata dena
# aur session.get("farm_id") ka actual value use karna.
DEFAULT_FARM_ID = 14


# ============================================================
# FEATURE 1: CROP ADVISORY AGENT
# ============================================================
def generate_crop_advisory(farm_id):
    """
    Weather forecast + latest NDVI dekh ke proactive advisory banata hai.
    Real deployment me ye function ek daily cron/celery task se bhi
    call ho sakta hai (sirf chat tool se nahi) taaki push notification
    bheji ja sake.
    """
    # TODO(you): apne actual weather + NDVI services se replace karo
    from services.weather import get_forecast          # expected: get_forecast(farm_id) -> dict
    from services.ndvi import get_latest_ndvi          # expected: get_latest_ndvi(farm_id) -> dict

    try:
        forecast = get_forecast(farm_id)
        ndvi = get_latest_ndvi(farm_id)
    except Exception as e:
        logger.warning(f"advisory data fetch failed: {e}")
        return {"advisory": "Abhi weather/NDVI data available nahi hai."}

    advisories = []
    if forecast.get("rain_expected_next_48h"):
        advisories.append("Agle 48 ghante me baarish ki sambhavna hai — spray ya khaad abhi mat daalo.")
    if ndvi.get("health_score", 1.0) < 0.4:
        advisories.append("NDVI score kam aa raha hai, fasal ka health check zaroor karo.")
    if forecast.get("temp_max", 0) > 40:
        advisories.append("Bahut garmi hai, extra paani ki zaroorat ho sakti hai.")

    if not advisories:
        advisories.append("Sab theek lag raha hai, koi khaas alert nahi hai abhi.")

    return {"advisory": " ".join(advisories), "raw": {"forecast": forecast, "ndvi": ndvi}}


# ============================================================
# FEATURE 2: EXPENSE / INCOME TRACKER
# ============================================================
def add_transaction(user_id, amount, category, txn_type):
    """
    txn_type: 'expense' ya 'income'
    TODO(you): apna actual model (models.transaction.Transaction) banao/import karo
    """
    from models.transaction import Transaction  # expected fields: user_id, amount, category, txn_type, created_at
    from extensions import db  # apka SQLAlchemy db instance

    txn = Transaction(
        user_id=user_id, amount=amount, category=category,
        txn_type=txn_type, created_at=datetime.utcnow()
    )
    db.session.add(txn)
    db.session.commit()
    return {"status": "recorded", "amount": amount, "category": category, "txn_type": txn_type}


def get_expense_summary(user_id, days=30):
    from models.transaction import Transaction
    since = datetime.utcnow() - timedelta(days=days)
    txns = Transaction.query.filter(
        Transaction.user_id == user_id, Transaction.created_at >= since
    ).all()

    income = sum(t.amount for t in txns if t.txn_type == "income")
    expense = sum(t.amount for t in txns if t.txn_type == "expense")
    return {
        "days": days,
        "total_income": income,
        "total_expense": expense,
        "net": income - expense,
        "count": len(txns),
    }


# ============================================================
# FEATURE 3: LOAN / SCHEME ELIGIBILITY HELPER
# ============================================================
def check_loan_eligibility(user_id):
    """
    Farm history (yield, marketplace sales, land size) dekh ke
    personalized scheme/loan suggestion deta hai.
    TODO(you): actual eligibility rules apni government_schemes DB
    ke hisaab se refine karo — ye ek simple rule-based starting point hai.
    """
    from models.farm import Farm          # expected: land_size, crop_type
    from models.marketplace import Listing

    farm = Farm.query.filter_by(user_id=user_id).first()
    if not farm:
        return {"eligible_schemes": [], "note": "Pehle apna farm register karo taaki eligibility check ho sake."}

    total_sales = Listing.query.filter_by(
        user_id=user_id, listing_type="sell"
    ).count()

    eligible = []
    if farm.land_size and farm.land_size <= 2:
        eligible.append("PM-KISAN (small/marginal farmer)")
    if total_sales >= 3:
        eligible.append("Kisan Credit Card — regular selling history ke basis par")
    if not eligible:
        eligible.append("General crop insurance scheme (PMFBY) check karo")

    return {"eligible_schemes": eligible, "land_size": farm.land_size, "sales_count": total_sales}


# ============================================================
# FEATURE 4: PEST / DISEASE ALERT AGENT
# ============================================================
def get_nearby_disease_alerts(lat, lng, radius_km=10):
    """
    Nearby farms ke recent disease-detection reports check karta hai.
    TODO(you): apne crop-disease detection model ke results ek
    DiseaseReport table me save karo (farm_id, lat, lng, disease_name, created_at)
    taaki ye query kaam kare.
    """
    from models.disease_report import DiseaseReport
    from sqlalchemy import func

    since = datetime.utcnow() - timedelta(days=14)
    # Simplified bounding-box distance filter; production me PostGIS/haversine use karo
    reports = DiseaseReport.query.filter(DiseaseReport.created_at >= since).all()

    nearby = []
    for r in reports:
        # TODO(you): real haversine distance yahan lagao
        approx_dist_km = ((r.lat - lat) ** 2 + (r.lng - lng) ** 2) ** 0.5 * 111
        if approx_dist_km <= radius_km:
            nearby.append({"disease": r.disease_name, "distance_km": round(approx_dist_km, 1)})

    if not nearby:
        return {"count": 0, "summary": "Aapke area me abhi koi disease alert nahi hai."}

    summary = f"{len(nearby)} nearby farms me disease detect hua hai: " + \
              ", ".join(f"{n['disease']} ({n['distance_km']}km)" for n in nearby[:3])
    return {"count": len(nearby), "summary": summary, "alerts": nearby}


# ============================================================
# FEATURE 5: PRICE PREDICTION + SELLING ADVISOR
# ============================================================
def get_selling_advice(crop_name, mandi_id=None):
    """
    Mandi price trend dekh ke "abhi becho ya ruko" advice deta hai.
    TODO(you): apna existing mandi price prediction model/service
    yahan call karo — ye stub last N din ka simple trend nikaal raha hai.
    """
    from services.mandi_price import get_price_history  # expected: list of {"date":..., "price":...}

    history = get_price_history(crop_name, mandi_id, days=14)
    if not history or len(history) < 2:
        return {"advice": f"{crop_name} ke liye pryapt price history nahi hai abhi."}

    trend = history[-1]["price"] - history[0]["price"]
    pct_change = (trend / history[0]["price"]) * 100 if history[0]["price"] else 0

    if pct_change > 5:
        advice = f"{crop_name} ka bhav badh raha hai ({pct_change:.1f}%), thoda ruk sakte ho."
    elif pct_change < -5:
        advice = f"{crop_name} ka bhav gir raha hai ({pct_change:.1f}%), abhi bech dena behtar hoga."
    else:
        advice = f"{crop_name} ka bhav stable hai, jab suvidha ho tab bech sakte ho."

    return {"advice": advice, "current_price": history[-1]["price"], "pct_change_14d": round(pct_change, 1)}


# ============================================================
# FEATURE 7: COMMUNITY Q&A (RAG-style retrieval)
# ============================================================
def search_community_qa(query_text):
    """
    Purane solved farmer problems ke database me simple keyword/embedding
    search karta hai. TODO(you): production me ye pgvector/FAISS jaisa
    proper vector search hona chahiye — ye stub sirf keyword match hai.
    """
    from models.community_qa import CommunityPost  # expected: question, answer, village, created_at

    posts = CommunityPost.query.filter(
        CommunityPost.question.ilike(f"%{query_text}%")
    ).order_by(CommunityPost.created_at.desc()).limit(3).all()

    if not posts:
        return {"count": 0, "summary": "Isse milta julta koi purana sawaal-jawab nahi mila."}

    summary = "; ".join(f"{p.village}: {p.answer[:80]}" for p in posts)
    return {"count": len(posts), "summary": summary}


# ============================================================
# FEATURE 8: ONBOARDING AGENT
# ============================================================
def save_onboarding_profile(user_id, crop_type=None, land_size=None, village=None):
    """
    Conversation ke through collected info se farmer profile banata/update karta hai.
    TODO(you): apna actual User/Farm model yahan use karo.
    """
    from models.farm import Farm
    from extensions import db

    farm = Farm.query.filter_by(user_id=user_id).first()
    if not farm:
        farm = Farm(user_id=user_id)
        db.session.add(farm)

    if crop_type:
        farm.crop_type = crop_type
    if land_size:
        farm.land_size = land_size
    if village:
        farm.village = village

    db.session.commit()
    return {"status": "saved", "crop_type": farm.crop_type, "land_size": farm.land_size, "village": farm.village}


# ============================================================
# EXISTING FEATURE: MARKETPLACE LISTINGS
# ============================================================
def get_marketplace_listings(listing_type):
    from models.marketplace import Listing
    listings = Listing.query.filter_by(listing_type=listing_type).order_by(Listing.created_at.desc()).limit(5).all()
    if not listings:
        return {"count": 0, "summary": "Abhi koi listing available nahi hai"}
    summary = "; ".join([f"{l.crop_name} {l.quantity} @ ₹{l.price}" for l in listings])
    return {"count": len(listings), "summary": summary}


def create_marketplace_listing(user_id, crop_name, quantity, price, listing_type):
    """
    NAYA: voice se seedha listing create karne ka tool.
    Confirmation frontend se pehle already ho chuki maani gayi hai
    (agent_endpoint me confirm-step handle hota hai, neeche dekho).
    """
    from models.marketplace import Listing
    from extensions import db

    listing = Listing(
        user_id=user_id, crop_name=crop_name, quantity=quantity,
        price=price, listing_type=listing_type, created_at=datetime.utcnow()
    )
    db.session.add(listing)
    db.session.commit()
    return {"status": "created", "crop_name": crop_name, "quantity": quantity, "price": price}


# ---------------------------------------------------------
# DATA TOOL MAP — simple (non-navigation) tools jinka result
# seedha "tool" role message ban jata hai
# ---------------------------------------------------------
DATA_TOOL_MAP = {
    "get_marketplace_listings": get_marketplace_listings,
}


# ---------------------------------------------------------
# TOOL DEFINITIONS (OpenAI function-calling schema)
# ---------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": (
                "User ke bataye gaye page/feature par navigate karta hai bina "
                "unhe click/touch kiye. Jab user bole 'X dikhao', 'X kholo', "
                "'X pe le chalo', is tool ko call karo panel_name ke saath."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "panel_name": {
                        "type": "string",
                        "enum": [
                            "dashboard", "mandi_price", "disease_detection",
                            "schemes", "marketplace", "weather", "farm_map",
                            "expenses", "community"
                        ]
                    }
                },
                "required": ["panel_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_location",
            "description": "User ki current GPS location map par dikhata hai.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearby_mandi",
            "description": "User ki GPS location ke basis par sabse nazdeek mandis (3 tak) dhoondta hai.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_marketplace_listings",
            "description": "Sell ya buy listings ki summary deta hai.",
            "parameters": {
                "type": "object",
                "properties": {"listing_type": {"type": "string", "enum": ["sell", "buy"]}},
                "required": ["listing_type"]
            }
        }
    },
    # ---- NAYE TOOLS ----
    {
        "type": "function",
        "function": {
            "name": "get_crop_advisory",
            "description": (
                "Weather + NDVI dekh ke fasal ki proactive salah deta hai. "
                "Jab user bole 'aaj kya karu', 'fasal ke liye salah do', "
                "'kuch alert hai kya', is tool ko call karo."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_transaction",
            "description": (
                "User ka kharcha ya kamai record karta hai. Jab user bole "
                "'500 rupaye beej pe kharch kiye', 'aaj 2000 kamaye', is tool call karo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "category": {"type": "string", "description": "jaise: beej, khaad, majdoori, bikri"},
                    "txn_type": {"type": "string", "enum": ["income", "expense"]}
                },
                "required": ["amount", "category", "txn_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_summary",
            "description": "Pichle N dino ka kharcha-kamai ka summary deta hai. Jab user pooche 'is mahine kitna kharcha hua'.",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "default 30"}}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_loan_eligibility",
            "description": (
                "Farm history dekh ke personalized loan/scheme eligibility batata hai. "
                "Jab user bole 'main kaunsi yojana ke liye eligible hoon', 'loan mil sakta hai kya'."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearby_disease_alerts",
            "description": (
                "User ki location ke aas-paas recent disease/pest reports check karta hai. "
                "Jab user bole 'area me koi bimari failh rahi hai kya'."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_selling_advice",
            "description": (
                "Mandi price trend dekh ke 'abhi bechu ya ruko' advice deta hai. "
                "Jab user bole 'abhi bechu ya ruko', 'price aage badhega kya'."
            ),
            "parameters": {
                "type": "object",
                "properties": {"crop_name": {"type": "string"}},
                "required": ["crop_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_community_qa",
            "description": (
                "Dusre farmers ke solved problems ke database me milta julta sawaal dhoondta hai. "
                "Jab user koi khaas farming problem bataye jiska seedha answer na ho."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query_text": {"type": "string"}},
                "required": ["query_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_onboarding_profile",
            "description": (
                "Naye user ki profile (crop, land size, village) conversation se save karta hai. "
                "Jab naya user apni fasal/zameen/gaon ke baare me bataye."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "crop_type": {"type": "string"},
                    "land_size": {"type": "number", "description": "acres me"},
                    "village": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_marketplace_listing",
            "description": (
                "User ki fasal ki naya sell/buy listing banata hai. Sirf tabhi call karo "
                "jab user ne pehle hi confirm kar diya ho (e.g. 'haan pakka' ke baad). "
                "Agar confirm nahi hua hai to pehle confirmation maango, ye tool mat call karo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "crop_name": {"type": "string"},
                    "quantity": {"type": "string", "description": "jaise '50 kg'"},
                    "price": {"type": "number"},
                    "listing_type": {"type": "string", "enum": ["sell", "buy"]}
                },
                "required": ["crop_name", "quantity", "price", "listing_type"]
            }
        }
    },
]


# ---------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------
SYSTEM_PROMPT = """Tum KrishiSeva AI ho, ek farmer-friendly voice assistant.
Hinglish me short, warm jawab do (1-2 lines, kyunki ye bola bhi jayega).
Agar user ki language Marathi lage, Marathi me hi jawab do.

NAVIGATION (navigate_to):
- "dashboard", "NDVI", "meri fasal ki sehat" -> dashboard
- "mandi price", "bhav", "rate" -> mandi_price
- "bimari", "disease", "fasal check karo" -> disease_detection
- "sarkari yojana", "scheme", "subsidy" -> schemes
- "bechna hai", "khareedna hai", "marketplace" -> marketplace
- "mausam", "weather" -> weather
- "naksha", "farm map", "GPS" -> farm_map
- "kharcha", "expenses", "hisaab" -> expenses
- "community", "doosre kisan" -> community

DIRECT DATA TOOLS (in cheezon ke liye seedha page pe navigate mat karo,
data fetch karke seedha bol do):
- "kya bik raha hai/khareeda ja raha hai" -> get_marketplace_listings
- "aaj kya karu / koi alert hai" -> get_crop_advisory
- "X rupaye kharch/kamaye" -> add_transaction
- "is mahine kitna kharcha hua" -> get_expense_summary
- "kaunsi yojana/loan ke liye eligible hoon" -> check_loan_eligibility
- "area me bimari failh rahi hai kya" -> get_nearby_disease_alerts
- "abhi bechu ya ruko" -> get_selling_advice
- koi specific farming samasya jiska seedha jawab na ho -> search_community_qa
- naya user apni fasal/zameen/gaon bataye -> save_onboarding_profile

LOCATION:
- "mera location dikhao", "main kahan hoon" -> show_location
- "nazdeek mandi", "kahan bechne jaun" -> find_nearby_mandi

MARKETPLACE LISTING CREATE KARNA (SENSITIVE ACTION):
Agar user bole "mujhe X bechna/khareedna hai Y price me", pehle
confirm karo: "Pakka Y price me X bechna hai?" Sirf jab user "haan/pakka/confirm"
bole, tabhi create_marketplace_listing tool call karo. Bina confirm kiye
kabhi ye tool mat call karo.
"""


# ---------------------------------------------------------
# HELPER: safe OpenAI call with retry-free error handling
# ---------------------------------------------------------
def safe_chat_completion(**kwargs):
    try:
        return client.chat.completions.create(**kwargs)
    except APITimeoutError:
        logger.error("OpenAI request timed out")
        return None
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling OpenAI: {e}")
        return None


# ---------------------------------------------------------
# AGENT ENDPOINT
# ---------------------------------------------------------
@agent_bp.route("/api/agent", methods=["POST"])
# @login_required  # TEMP: debugging ke liye hata diya — testing ke baad wapas lagao
def agent_endpoint():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    history = data.get("history") or []
    user_location = data.get("location")  # {"lat": ..., "lng": ...} ya None
    user_id = session.get("user_id")

    if not user_message:
        return jsonify({"reply": "Kuch bolo ya likho, main sun raha hoon.", "actions": []}), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if user_location:
        messages.append({
            "role": "system",
            "content": f"User ki current location: lat={user_location.get('lat')}, lng={user_location.get('lng')}."
        })

    # history validation (missing keys se crash na ho)
    for turn in history[-10:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    # collect ALL actions instead of overwriting (fix #3 from pehle ki review)
    ui_actions = []

    response = safe_chat_completion(
        model=MODEL_NAME, messages=messages, tools=TOOLS, tool_choice="auto"
    )
    if response is None:
        return jsonify({
            "reply": "Abhi thodi dikkat aa rahi hai, thodi der me phir try karo.",
            "actions": []
        }), 503

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                fn_args = {}

            try:
                if fn_name == "navigate_to":
                    panel_name = fn_args.get("panel_name")
                    if panel_name == "dashboard":
                        # Login abhi nahi hai, isliye session me farm_id set nahi
                        # hota — tab tak current/default farm_id=14 use karo,
                        # taaki "dashboard dikhao" bolne par seedha
                        # http://127.0.0.1:5000/dashboard/14 khule.
                        # TODO(you): jab proper user/farm mapping ho jaye,
                        # session.get("farm_id") ka actual value use karna.
                        farm_id = session.get("farm_id") or DEFAULT_FARM_ID
                        url = f"/dashboard/{farm_id}"
                    else:
                        url = STATIC_ROUTES.get(panel_name, "/")
                    ui_actions.append({"action": "navigate", "params": {"url": url}})
                    tool_result = {"status": "navigating", "url": url}

                elif fn_name == "show_location":
                    ui_actions.append({"action": "show_location", "params": {}})
                    tool_result = {"status": "showing_location"}

                elif fn_name == "find_nearby_mandi":
                    if user_location:
                        nearby = find_nearby_mandis(user_location["lat"], user_location["lng"], top_n=3)
                        ui_actions.append({"action": "show_nearby_mandi", "params": {"mandis": nearby}})
                        tool_result = {"nearby_mandis": nearby}
                    else:
                        tool_result = {"error": "Location abhi available nahi hai, pehle location share karo"}

                elif fn_name == "get_crop_advisory":
                    farm_id = session.get("farm_id") or DEFAULT_FARM_ID
                    tool_result = generate_crop_advisory(farm_id)

                elif fn_name == "add_transaction":
                    tool_result = add_transaction(
                        user_id, fn_args.get("amount"), fn_args.get("category"), fn_args.get("txn_type")
                    )

                elif fn_name == "get_expense_summary":
                    tool_result = get_expense_summary(user_id, fn_args.get("days", 30))

                elif fn_name == "check_loan_eligibility":
                    tool_result = check_loan_eligibility(user_id)

                elif fn_name == "get_nearby_disease_alerts":
                    if user_location:
                        tool_result = get_nearby_disease_alerts(user_location["lat"], user_location["lng"])
                    else:
                        tool_result = {"error": "Location abhi available nahi hai"}

                elif fn_name == "get_selling_advice":
                    tool_result = get_selling_advice(fn_args.get("crop_name"))

                elif fn_name == "search_community_qa":
                    tool_result = search_community_qa(fn_args.get("query_text", ""))

                elif fn_name == "save_onboarding_profile":
                    tool_result = save_onboarding_profile(
                        user_id, fn_args.get("crop_type"), fn_args.get("land_size"), fn_args.get("village")
                    )
                    ui_actions.append({"action": "onboarding_saved", "params": tool_result})

                elif fn_name == "create_marketplace_listing":
                    tool_result = create_marketplace_listing(
                        user_id, fn_args.get("crop_name"), fn_args.get("quantity"),
                        fn_args.get("price"), fn_args.get("listing_type")
                    )
                    ui_actions.append({"action": "listing_created", "params": tool_result})

                elif fn_name in DATA_TOOL_MAP:
                    tool_result = DATA_TOOL_MAP[fn_name](**fn_args)

                else:
                    tool_result = {"error": f"Unknown tool {fn_name}"}

            except Exception as e:
                logger.exception(f"Tool '{fn_name}' failed")
                tool_result = {"error": "Is kaam ko karte waqt dikkat aayi."}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, default=str)
            })

        final_response = safe_chat_completion(
            model=MODEL_NAME, messages=messages, max_tokens=MAX_TOKENS_FINAL
        )
        if final_response is None:
            reply_text = "Kaam ho gaya, par jawab likhne me dikkat aa rahi hai."
        else:
            reply_text = final_response.choices[0].message.content or "Ji, ho gaya!"
    else:
        reply_text = msg.content or "Thoda aur bata sakte ho?"

    return jsonify({
        "reply": reply_text,
        "actions": ui_actions,          # list ab — multiple actions supported
        # backward-compat fields for older frontend code:
        "action": ui_actions[0]["action"] if ui_actions else None,
        "params": ui_actions[0]["params"] if ui_actions else None,
    })


# ============================================================
# FEATURE 6: WHATSAPP / SMS FALLBACK
# ============================================================
"""
Isi agent logic ko WhatsApp Business API (Meta Cloud API) ya Twilio
se expose karne ke liye ek alag webhook route. Real number/token
apne .env me daalo: WHATSAPP_TOKEN, WHATSAPP_PHONE_ID.

TODO(you): user ko phone number se account se map karna hoga
(models.user me phone_number column chahiye).
"""
import requests  # noqa: E402

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "krishiseva-verify")


@agent_bp.route("/api/whatsapp/webhook", methods=["GET"])
def whatsapp_verify():
    """Meta webhook verification handshake."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@agent_bp.route("/api/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook():
    payload = request.get_json(silent=True) or {}
    try:
        entry = payload["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        from_number = message["from"]
        text_body = message.get("text", {}).get("body", "")
    except (KeyError, IndexError):
        return jsonify({"status": "ignored"}), 200

    # TODO(you): from_number se apna user_id resolve karo
    # user = User.query.filter_by(phone_number=from_number).first()
    # Yahan hum simplified/no-auth version dikha rahe hain — production me
    # user resolve na ho to reply me "pehle app me register karo" bhejo.

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text_body},
    ]
    response = safe_chat_completion(model=MODEL_NAME, messages=messages, max_tokens=MAX_TOKENS_FINAL)
    reply_text = (response.choices[0].message.content if response else None) or "Abhi jawab nahi de paa raha, thodi der me try karo."

    send_whatsapp_message(from_number, reply_text)
    return jsonify({"status": "ok"}), 200


def send_whatsapp_message(to_number, text):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_ID):
        logger.warning("WhatsApp credentials missing, skipping send")
        return
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    body = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    try:
        requests.post(url, headers=headers, json=body, timeout=10)
    except requests.RequestException as e:
        logger.error(f"WhatsApp send failed: {e}")