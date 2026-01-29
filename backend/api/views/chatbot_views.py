import logging
import json
import re
import unicodedata
from datetime import datetime, timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta 

from rest_framework.test import APIRequestFactory
from rest_framework.permissions import IsAuthenticated

from backend.api.views.weather_intent_views import weather_by_intent
from backend.api.permissions.is_premium_user import IsPremiumUser
from backend.api.services.weather_response_generator import (
    generate_weather_response
)

from openai import OpenAI

logger = logging.getLogger(__name__)

# ---------------------
# OPENAI GPT-4o API KEY
# ---------------------
OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------
# Remove accents (backup normalization)
# ---------------------
def remove_accents(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

# ---------------------
# Normalize and tokenize
# ---------------------
def normalize_and_tokenize(text: str):
    """
    Normalize text for safe keyword matching:
    - lowercase
    - collapse spaces
    - tokenize into words
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    tokens = re.findall(r"[a-z0-9']+", text)
    return text, tokens


# ---------------------
# MATCH KEYWORDS EXACTLY
# ---------------------
def match_keywords_exact(text: str, tokens: list, keywords: list):
    """
    Matching rules:
    - Single-word keyword: must match exactly one token
    - Multi-word keyword: must match the full phrase with word boundaries
    """
    for kw in keywords:
        kw = kw.lower().strip()

        if " " in kw:
            # multi-word phrase: match full phrase
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, text):
                return True
        else:
            # single-word: match token exactly
            if kw in tokens:
                return True

    return False



# ---------------------
# PROMPT (GIỮ NGUYÊN 100%)
# ---------------------
INTENT_PROMPT = f"""
You are an advanced intent extraction AI. 
The input question MUST be written in English. 
If the input is not English, reply with EXACT STRING:

"Your question must be in English and related to weather or natural disasters, which are the domains I can work with!"

Your job: extract meaning from English weather-related or natural-disaster-related questions.


RULES:

1) LANGUAGE CHECK:
- If the user input is NOT in English → STOP and return the error string above.

2) LOCATION:
- Extract the city/province clearly.
- If no valid location → location = null.

3) DATE & TIME:
- Convert detected dates to ISO format YYYY-MM-DD.
- If the date contains NO year → infer future year.
- Detect time-of-day keywords.

4) INTENTS:
- Specific date → include "daily_aggregation".
- today/tomorrow → include "weather_overview" + "weather_forecast".
- week/month → include "weather_forecast".
- No date → include "weather_overview".
- Travel/activity → include "activity_recommendation".
- Disaster-related keywords → include "disaster".
- Air condition, air pollution keywords -> include "air_pollution".
- Health issues, advice when sick → include "healthcare".

5) OUTPUT:
- JSON ONLY.are
"""

# ---------------------
# FUNCTION CALLING SCHEMA
# ---------------------
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
# STEP 3 – WEATHER FUNCTION DEFINITIONS (NEW)
# =====================================================

WEATHER_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "weather_overview",
            "description": "Get current weather overview, call this function when intent includes weather_overview",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "weather_forecast",
            "description": "Get weather forecast for a specific date, call this function when intent includes weather_forecast",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "day": {"type": ["string", "null"]}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "daily_aggregation",
            "description": "Get daily weather summary for a specific date, call this function when intent includes daily_aggregation",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "day": {"type": "string"}
                },
                "required": ["location", "day"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "air_pollution",
            "description": "Get air pollution forecast, call this function when intent includes air_pollution",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "day": {"type": "string"}
                },
                "required": ["location", "day"]
            }
        }
    }
]

# ---------------------
# TIMEZONE HELPERS (GIỮ NGUYÊN)
# ---------------------
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
        tz_string = (
            weather
            .get("data", {})
            .get("weather_overview", {})
            .get("tz")
        )
        if tz_string:
            return int(tz_string.split(":")[0])
    except Exception as e:
        logger.warning(f"Timezone detect failed: {e}")
    return 0

# ---------------------
# Greeting / Farewell detector (GIỮ NGUYÊN)
# ---------------------
def detect_greeting_or_farewell(message: str):
    msg = message.lower().strip()

    thanks = [
        "thanks", "thank you", "thx", "thank u",
        "appreciate it", "much appreciated","appreciate"
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


# ---------------------
# API: Analyze Intent
# ---------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPremiumUser])
def analyze_intent(request):

    user_message = request.data.get("message", "")
    if not user_message:
        return Response({"error": "message is required"}, status=400)

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

        # =====================================================
        # 🔥 GPT-4o FUNCTION CALLING (THAY GEMINI – DUY NHẤT)
        # =====================================================
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": user_message}
            ],
            tools=[{"type": "function", "function": WEATHER_INTENT_FUNCTION}],
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return Response(
                {"error": "Your question must be in English and related to weather, which is the domain I can work with!"},
                status=400
            )

        result = json.loads(message.tool_calls[0].function.arguments)

        logger.debug(f"[GPT-4o Intent JSON] {json.dumps(result, indent=2)}")

 # ---------------------
        # Python backup: generate location_ascii
        # ---------------------
        if result.get("location"):
            result["location_ascii"] = remove_accents(result["location"])
        else:
            return Response(
                {"error": "Your question must be in English and must contain a valid location."},
                status=400
            )

        # ---------------------
        # NEW FEATURE: detect disaster intent
        # ---------------------
        msg_lower, tokens = normalize_and_tokenize(user_message)

        disaster_keywords = [
            "typhoon", "storm", "super typhoon", "hurricane", "cyclone",
            "flood", "tsunami", "tornado", "earthquake",
            "wildfire", "thunderstorm", "landslide",
            "extreme weather", "natural disaster", "disaster"
        ]

        intents = result.get("intent", [])

        if match_keywords_exact(msg_lower, tokens, disaster_keywords):
            if "disaster" not in intents:
                intents.append("disaster")

        result["intent"] = intents
        
        # ---------------------
        # NEW FEATURE: detect air pollution intent
        # ---------------------
        msg_lower, tokens = normalize_and_tokenize(user_message)

        air_pollution_keywords = [
            "air quality",
            "air pollution",
            "pollution",
            "aqi",
            "pm2.5",
            "pm10",
            "smog",
            "haze",
            "fine particles",
            "dust storm",
            "respiratory problem",
            "breathing problem"
        ]

        intents = result.get("intent", [])

        if match_keywords_exact(msg_lower, tokens, air_pollution_keywords):
            if "air_pollution" not in intents:
                intents.append("air_pollution")

        result["intent"] = intents
        
        # ---------------------
        # NEW FEATURE: detect healthcare intent
        # ---------------------
        msg_lower, tokens = normalize_and_tokenize(user_message)

        healthcare_keywords = [
            "fever", "sick", "ill", "illness",
            "headache", "cold", "flu",
            "cough", "sore throat", "runny nose",
            "fatigue", "tired", "weak",
            "nausea", "vomit", "dizzy", "dizziness",
            "medical advice",
            "health problem",
            "healthcare advice"
        ]

        intents = result.get("intent", [])

        if match_keywords_exact(msg_lower, tokens, healthcare_keywords):
            if "healthcare" not in intents:
                intents.append("healthcare")

        result["intent"] = intents

        # ------------------------------------------
        # 3.1 FIX QUAN TRỌNG: ĐÚNG NGÀY "TODAY"
        # ------------------------------------------
        msg_lower, tokens = normalize_and_tokenize(user_message)
        today_keywords = [
            "today", "right now", "this day", "currently",
            "at the moment", "nowadays", "current day", "now", "tonight", "present day",
            "this morning", "this afternoon", "this evening", "this night"
        ]

        utc_offset_hours = get_city_utc_offset_hours(
            result.get("location_ascii")
        )
        system_today = get_local_today_by_utc_offset(utc_offset_hours)

        if match_keywords_exact(msg_lower, tokens, today_keywords):
            # override day
            result["day"] = system_today.strftime("%Y-%m-%d")
            if "weather_forecast" not in intents:
                intents.append("weather_forecast")
            if "weather_overview" not in intents:
                intents.append("weather_overview")
            result["intent"] = intents

         # ------------------------------------------
        # 3. FIX QUAN TRỌNG: ĐÚNG NGÀY "TOMORROW"
        # ------------------------------------------
        msg_lower, tokens = normalize_and_tokenize(user_message)
        tomorrow_keywords = [
            "tomorrow", "tommorow", "tommorrow", 
            "tmrw", "tomo", "next day", 
            "the next day", "the day after today"
        ]

        system_tomorrow = system_today + timedelta(days=1)

        if match_keywords_exact(msg_lower, tokens, tomorrow_keywords):
            # override day
            result["day"] = system_tomorrow.strftime("%Y-%m-%d")
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
                
        
        NON_WEATHER_INTENTS = {
            "activity_recommendation",
            "disaster",
            "healthcare"
        }

        weather_intents = [
            i for i in result["intent"]
            if i not in NON_WEATHER_INTENTS
        ]

        # =====================================================
        # STEP 4 – LLM DECIDES WEATHER TOOL CALLS (MULTI TOOL)
        # =====================================================

        tool_planner_messages = [
            {
                "role": "system",
                "content": (
                    "You are a STRICT weather tool planner.\n"
                    "ONLY call tools that already exist in intent[].\n"
                    "DO NOT add new tools.\n"
                    "DO NOT remove any intent.\n"
                    "One intent corresponds to one tool call.\n"
                    "Return tool calls only."
                )
            },
            {
                "role": "user",
                "content": json.dumps({
                    "intent": [
                        i for i in result["intent"]
                        if i in ["weather_overview", "weather_forecast", "daily_aggregation", "air_pollution"]
                    ],
                    "location": result["location"],
                    "day": result["day"]
                })
            }
        ]

        tool_plan = client.chat.completions.create(
            model="gpt-4o",
            messages=tool_planner_messages,
            tools=WEATHER_FUNCTIONS,
            tool_choice="auto"
        )

        tool_calls = tool_plan.choices[0].message.tool_calls or []

        logger.debug("===== WEATHER TOOL CALLS =====")
        for call in tool_calls:
            logger.debug(
                f"{call.function.name} -> {call.function.arguments}"
            )

        # =====================================================
        # STEP 5 – EXECUTE WEATHER TOOLS
        # =====================================================

        weather_data = {}

        for call in tool_calls:
            args = json.loads(call.function.arguments)

            payload = {
                "intent": [call.function.name],
                "location": args.get("location"),
                "location_ascii": remove_accents(args.get("location")),
                "day": args.get("day"),
                "time_of_day": result.get("time_of_day")
            }

            try:
                response = call_weather_router(payload)
                weather_data[call.function.name] = response.get("data", {})
            except Exception as e:
                logger.error(
                    f"Tool execution failed: {call.function.name}",
                    exc_info=True
                )

        # ============================
        # 🔥 STEP 4 – LLM RESPONSE 🔥
        # ============================
        final_answer = None

        try:
            final_answer = generate_weather_response(
            user_question=user_message,
            intent_result=result,
            weather_data=weather_data
        )
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}", exc_info=True)

        final_response = {
            "intent_result": result,
            "weather": weather_data,
            "answer": final_answer
        }

        return Response(final_response, status=200)


    except Exception as e:
        logger.error(f"Chatbot intent error: {e}", exc_info=True)
        return Response({"error": str(e)}, status=500)
    

def call_weather_router(intent_json):
    """
    Internal call to weather_by_intent
    Không phải HTTP call → gọi trực tiếp view
    """
    factory = APIRequestFactory()
    fake_request = factory.post(
        "/api/weather/by-intent/",
        data=intent_json,
        format="json"
    )

    response = weather_by_intent(fake_request)
    return response.data