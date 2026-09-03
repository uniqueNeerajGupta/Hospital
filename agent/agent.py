import os
import json
from openai import OpenAI
from models.farm import Farm
from services.weather_service import get_weather
from services.mandi_prediction import predict_mandi_price
from services.disease_risk import predict_disease_risk
from services.location_service import get_center_point

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Tum KrishiSeva AI ho — chhote aur marginal kisano ke liye ek voice assistant.
Hamesha SIMPLE Hindi (Devanagari) mein jawab do, chhote sentences mein, kyunki ye jawab bola (TTS) jayega.
Agar user ka sawaal farm/weather/mandi price/disease se related hai, tools use karo or agar user value bolega feature.
Agar general sawaal hai (jaise "namaste", "tum kaun ho"), seedha jawab do.
Kabhi bhi English mein jawab mat do, jab tak user khud English mein na pooche.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Kisan ke khet ka current mausam batao (temperature, humidity, wind, rainfall)",
            "parameters": {
                "type": "object",
                "properties": {
                    "farm_id": {"type": "integer", "description": "Kisan ke khet ki ID"}
                },
                "required": ["farm_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_mandi_price",
            "description": "Kisi fasal ka mandi price predict karo",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {"type": "string"},
                    "district": {"type": "string"},
                    "market": {"type": "string"},
                    "commodity": {"type": "string", "description": "e.g. Wheat, Rice, Potato"},
                    "variety": {"type": "string"},
                    "month": {"type": "integer", "description": "1 se 12"}
                },
                "required": ["state", "district", "market", "commodity", "variety", "month"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_disease_risk",
            "description": "Khet ki fasal mein disease ka risk check karo",
            "parameters": {
                "type": "object",
                "properties": {
                    "farm_id": {"type": "integer"}
                },
                "required": ["farm_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_page",
            "description": "User ko website ke kisi page par le jao jab woh 'kholo/dikhao/le chalo' bole",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "string",
                        "enum": ["mandi", "weather", "map", "government_schemes", "recommendation"]
                    }
                },
                "required": ["page"]
            }
        }
    }
]


def execute_function(name, args):
    if name == "get_weather":
        farm = Farm.query.get(args["farm_id"])
        if not farm:
            return {"error": "Farm nahi mila"}
        lat, lng = get_center_point(farm.coordinates)
        return get_weather(lat, lng)

    if name == "predict_mandi_price":
        return predict_mandi_price(
            args["state"], args["district"], args["market"],
            args["commodity"], args["variety"], args["month"]
        )

    if name == "get_disease_risk":
        farm = Farm.query.get(args["farm_id"])
        if not farm:
            return {"error": "Farm nahi mila"}
        lat, lng = get_center_point(farm.coordinates)
        weather = get_weather(lat, lng)
        ndvi_score = 0.72  # TODO: latest NDVIHistory se lena
        return predict_disease_risk(
            ndvi_score, weather["humidity"], weather["temperature"], weather["rainfall"]
        )

    if name == "navigate_page":
        return {"status": "navigating", "page": args["page"]}

    return {"error": "Function nahi mila"}


def handle_voice_command(user_text, farm_id=None):
    context_note = f"\nCurrent farm_id: {farm_id}" if farm_id else "\nAbhi koi farm select nahi hai."

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + context_note},
        {"role": "user", "content": user_text}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    msg = response.choices[0].message
    action = None

    if msg.tool_calls:
        messages.append(msg)

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            result = execute_function(fn_name, fn_args)

            if fn_name == "navigate_page":
                action = {"type": "navigate", "page": fn_args["page"]}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        reply_text = final.choices[0].message.content
    else:
        reply_text = msg.content

    return {"reply": reply_text, "action": action}