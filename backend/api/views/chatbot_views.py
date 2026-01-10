import logging
import json
import re
import unicodedata
from datetime import datetime, timezone, timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIRequestFactory

from backend.api.views.weather_intent_views import weather_by_intent
from backend.api.permissions.is_premium_user import IsPremiumUser
from backend.api.services.weather_response_generator import generate_weather_response

from openai import OpenAI

logger = logging.getLogger(__name__)

# =====================================================
# OPENAI GPT-4o CONFIG
# =====================================================
OPENAI_API_KEY = "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"

client = OpenAI(api_key=OPENAI_API_KEY)

# =====================================================
# REMOVE ACCENTS (BACKUP NORMALIZATION)
# =====================================================
def remove_accents(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

# =====================================================
# DATE / TIME HELPERS (GIỮ NGUYÊN)
# =====================================================
def get_local_today_by_utc_offset(utc_offset_hours: int):
    tz = timezone(timedelta(hours=utc_offset_hours))
    return datetime.now(tz).date()

def get_city_utc_offset_hours(location_ascii):
    try:
        dummy_payload = {
            "location": location_ascii,
            "location_ascii": location_ascii,
            "intent": ["weather_overview"],
            "day": None,
            "time_of_day": None
        }
        weather = call_weather_router(dummy_payload)
        tz_string = weather.get("data", {}).get("weather_overview", {}).get("tz")
        if tz_string:
            return int(tz_string.split(":")[0])
    except Exception as e:
        logger.warning(f"Timezone detect failed: {e}")
    return 0

# =====================================================
# GREETING / FAREWELL DETECTOR (GIỮ NGUYÊN)
# =====================================================
def detect_greeting_or_farewell(message: str):
    msg = message.lower().strip()
    thanks = [
        "thanks", "thank you", "thx", "thank u",
        "appreciate it", "much appreciated", "appreciate"
    ]
    farewells = [
        "bye", "goodbye", "see you", "see ya",
        "farewell", "take care"
    ]
    for t in thanks:
        if msg == t or msg.startswith(t):
            return "thanks"
    for f in farewells:
        if msg == f or msg.startswith(f):
            return "farewell"
    return None

# =====================================================
# FUNCTION CALLING SCHEMA
# =====================================================
WEATHER_INTENT_FUNCTION = {
    "name": "extract_weather_intent",
    "description": "Extract structured weather intent from English user question",
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "array",
                "items": {"type": "string"}
            },
            "location": {"type": ["string", "null"]},
            "location_ascii": {"type": ["string", "null"]},
            "day": {"type": ["string", "null"]},
            "time_of_day": {
                "type": ["string", "null"],
                "enum": ["morning", "afternoon", "evening", "night", None]
            }
        },
        "required": ["intent", "location", "day", "time_of_day"]
    }
}

# =====================================================
# API: ANALYZE INTENT
# =====================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPremiumUser])
def analyze_intent(request):

    user_message = request.data.get("message", "")
    if not user_message:
        return Response({"error": "message is required"}, status=400)

    # 🌟 GREETING / FAREWELL
    greeting_type = detect_greeting_or_farewell(user_message)
    if greeting_type == "thanks":
        return Response({
            "answer": "You’re very welcome! 😊 If you need any weather information, health or travel advice base on weather, I’m always here to help."
        }, status=200)

    if greeting_type == "farewell":
        return Response({
            "answer": "Goodbye! 👋 Have a great day, and feel free to come back whenever you need weather updates."
        }, status=200)

    try:
        logger.debug(f"[Chatbot] Analyze Intent: {user_message}")

        # ============================
        # 🔥 GPT-4o FUNCTION CALLING
        # ============================
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intent extraction AI.\n"
                        "Input MUST be English.\n"
                        "If not English → DO NOT CALL FUNCTION.\n\n"
                        
                        "INTENT RULES:\n"

                        "1) LOCATION:\n"
                        "- Extract the city/province clearly."
                        "- If no valid location → location = null.\n\n"

                        "2) DATE & TIME:\n"
                        "- Convert detected dates to ISO format YYYY-MM-DD.\n"
                        "- If the date contains NO year → infer future year.\n"
                        "- Detect time-of-day keywords."
                        
                        "3) INTENT TYPES:\n"
                        "- Specific date → daily_aggregation\n"
                        "- today/tomorrow → weather_overview + weather_forecast\n"
                        "- week/month → weather_forecast\n"
                        "- No date → weather_overview\n"
                        "- Travel/activity → activity_recommendation\n"
                        "- Disaster keywords → disaster\n"
                        "- Air quality keywords → air_pollution\n"
                        "- Health issues → healthcare"

                        "5) OUTPUT:\n"
                        "- JSON ONLY.\n"    
                    )
                },
                {"role": "user", "content": user_message}
            ],
            tools=[{"type": "function", "function": WEATHER_INTENT_FUNCTION}],
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return Response({
                "error": "Your question must be in English and related to weather, natural disasters, air quality or healthcare!."
            }, status=400)

        tool_args = json.loads(message.tool_calls[0].function.arguments)
        result = tool_args

        logger.debug(f"[GPT-4o Intent JSON] {json.dumps(result, indent=2)}")

        # ============================
        # PYTHON BACKUP LOGIC (GIỮ NGUYÊN)
        # ============================
        if not result.get("location"):
            return Response(
                {"error": "Your question must contain a valid location."},
                status=400
            )

        result["location_ascii"] = remove_accents(result["location"])
        msg_lower = user_message.lower()
        intents = result.get("intent", [])

        # --- DISASTER ---
        disaster_keywords = [
            "typhoon", "storm", "super typhoon", "hurricane", "cyclone",
            "flood", "tsunami", "tornado", "earthquake",
            "wildfire", "thunderstorm", "landslide",
            "extreme weather", "natural disaster", "disaster"
        ]
        msg_lower = user_message.lower()
        intents = result.get("intent", [])
        
        if any(k in msg_lower for k in disaster_keywords):
            if "disaster" not in intents:
                intents.append("disaster")
        
        result["intent"] = intents

        # --- AIR POLLUTION ---
        air_pollution_keywords = [
             "air quality", "air pollution", "pollution",
            "aqi", "pm2.5", "pm10",
            "smog", "haze", "dust",
            "fine particles", "air condition",
            "breathing", "respiratory"
        ]
        msg_lower = user_message.lower()
        intents = result.get("intent", [])
        
        if any(k in msg_lower for k in air_pollution_keywords):
            if "air_pollution" not in intents:
                intents.append("air_pollution")
                
        result["intent"] = intents

        # --- HEALTHCARE ---
        healthcare_keywords = [
             "fever", "sick", "ill", "illness",
            "headache", "cold", "flu",
            "cough", "sore throat", "runny nose",
            "fatigue", "tired", "weak",
            "nausea", "vomit", "dizzy", "dizziness",
            "health", "healthcare", "medical"
        ]
        
        msg_lower = user_message.lower()
        intents = result.get("intent", [])
        
        if any(k in msg_lower for k in healthcare_keywords):
            if "healthcare" not in intents:
                intents.append("healthcare")

        result["intent"] = intents

        # ============================
        # TODAY / TOMORROW OVERRIDE
        # ============================
        utc_offset = get_city_utc_offset_hours(result["location_ascii"])
        system_today = get_local_today_by_utc_offset(utc_offset)

           # ------------------------------------------
        # 3.1 FIX QUAN TRỌNG: ĐÚNG NGÀY "TODAY"
        # ------------------------------------------
        today_keywords = [
            "today", "right now", "this day", "currently",
            "at the moment", "nowadays", "current day", "now", "tonight", "this", "present day"
            "this morning", "this afternoon", "this evening", "this night"
        ]

        utc_offset_hours = get_city_utc_offset_hours(
            result.get("location_ascii")
        )
        system_today = get_local_today_by_utc_offset(utc_offset_hours)

        if any(k in msg_lower for k in today_keywords):

            # 👉 OVERRIDE day từ Gemini
            result["day"] = system_today.strftime("%Y-%m-%d")

            if "weather_forecast" not in intents:
                intents.append("weather_forecast")
            if "weather_overview" not in intents:
                intents.append("weather_overview")

            result["intent"] = intents
        
        tomorrow_keywords = [
            "tomorrow", "tommorow", "tommorrow", 
            "tmrw", "tomo", "next day", 
            "the next day", "the day after today"
        ]

        system_tomorrow = system_today + timedelta(days=1)

        if any(k in msg_lower for k in tomorrow_keywords):

            # → BỎ LUÔN NGÀY GEMINI, SET LẠI 100%
            result["day"] = system_tomorrow.strftime("%Y-%m-%d")

            # ép intent
            if "weather_forecast" not in intents:
                intents.append("weather_forecast")
            if "weather_overview" not in intents:
                intents.append("weather_overview")

            result["intent"] = intents
        # ---------------------
        # NEW: Handle "next week"
        # ---------------------
        msg_lower = user_message.lower()
        today = datetime.now()

        if ("next week" in msg_lower or "coming week" in msg_lower or "next weekend" in msg_lower):
            if result.get("day") is None:
                result["day"] = today.strftime("%Y-%m-%d")

            intents = result.get("intent", [])
            if "weather_forecast" not in intents:
                intents.append("weather_forecast")
            result["intent"] = intents

        # ---------------------
        # Python backup: infer missing weather_overview
        # ---------------------
        intents = result.get("intent", [])
        if result.get("day") is None and "weather_overview" not in intents:
            intents.append("weather_overview")
        result["intent"] = intents

        # ---------------------
        # Python backup: correct wrong year
        # ---------------------
        if result.get("day"):
            try:
                parsed = datetime.strptime(result["day"], "%Y-%m-%d")
                if parsed.year < today.year:
                    parsed = parsed.replace(year=today.year)
                    result["day"] = parsed.strftime("%Y-%m-%d")
            except:
                pass
            
                # ------------------------------------------
        # 4. FIX: DATE QUÁ XA (> 8 NGÀY) → KHÔNG FORECAST
        # ------------------------------------------
        if result.get("day"):
            try:
                target_day = datetime.strptime(
                    result["day"], "%Y-%m-%d"
                ).date()

                # local today theo city timezone
                utc_offset_hours = get_city_utc_offset_hours(
                    result.get("location_ascii")
                )
                local_today = get_local_today_by_utc_offset(
                    utc_offset_hours
                )

                day_diff = (target_day - local_today).days

                # OpenWeather forecast chỉ an toàn <= 8 ngày
                if abs(day_diff) > 8:
                    logger.info(
                        f"[Intent Adjust] Day {target_day} is {day_diff} days away → disable forecast"
                    )

                    intents = result.get("intent", [])

                    # remove forecast-related intents
                    intents = [
                        i for i in intents
                        if i not in ("weather_forecast", "weather_overview")
                    ]
                    # giữ lại air_pollution & disaster
                    if "air_pollution" not in intents and "air_pollution" in result.get("intent", []):
                        intents.append("air_pollution")

                    if "disaster" not in intents and "disaster" in result.get("intent", []):
                        intents.append("disaster")

                    # force daily aggregation
                    if "daily_aggregation" not in intents:
                        intents.append("daily_aggregation")

                    result["intent"] = intents

            except Exception as e:
                logger.warning(f"Date distance check failed: {e}")

        # ============================
        # AUTO CALL WEATHER API
        # ============================
        weather_data = None
        if any(i in result["intent"] for i in [
            "weather_forecast", "weather_overview", "daily_aggregation", "air_pollution"
        ]):
            try:
                weather_data = call_weather_router(result)
            except Exception as e:
                logger.error(f"Weather router error: {e}", exc_info=True)

        # ============================
        # STEP 4 – LLM RESPONSE
        # ============================
        final_answer = None
        
        final_answer = generate_weather_response(
            user_question=user_message,
            intent_result=result,
            weather_data=weather_data.get("data") if weather_data else {}
        )

        return Response({
            "intent_result": result,
            "weather": weather_data,
            "answer": final_answer
        }, status=200)

    except Exception as e:
        logger.error(f"Chatbot intent error: {e}", exc_info=True)
        return Response({"error": str(e)}, status=500)


# =====================================================
# INTERNAL WEATHER ROUTER
# =====================================================
def call_weather_router(intent_json):
    factory = APIRequestFactory()
    fake_request = factory.post(
        "/api/weather/by-intent/",
        data=intent_json,
        format="json"
    )
    response = weather_by_intent(fake_request)
    return response.data
