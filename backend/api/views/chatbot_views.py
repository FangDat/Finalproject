import logging
import json
import re
import unicodedata
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from google import genai
from google.cloud import aiplatform
from datetime import datetime, timedelta 


logger = logging.getLogger(__name__)

# ---------------------
# API KEY GEMINI 
# ---------------------
GEMINI_API_KEY = "AIzaSyC_nvEv1gM5SjwJT5D3EYb1RqMGQz-fCWA"

#AIzaSyBIMxmqjk-9sb7LPnB95kvbBXKnQcLkCkI
#AIzaSyDF8L7KU3jhUfCxD3PU6EVavb7afcUrLtI
#AIzaSyC_nvEv1gM5SjwJT5D3EYb1RqMGQz-fCWA

# ---------------------
# INIT GEMINI CLIENT
# ---------------------
client = genai.Client(api_key=GEMINI_API_KEY)


# ---------------------
# Remove accents (backup normalization)
# ---------------------
def remove_accents(text):
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


# ---------------------
# PROMPT
# ---------------------
INTENT_PROMPT = f"""
You are an advanced intent extraction AI. 
The input question MUST be written in English. 
If the input is not English, reply with EXACT STRING:

"Your question must be in English and related to weather or natural disasters, which are the domains I can work with!"

Your job: extract meaning from English weather-related or natural-disaster-related questions.

Output STRICT JSON with exactly this structure:

{{
  "intent": ["...", "..."],
  "location": "string or null",
  "location_ascii": "string or null",
  "day": "YYYY-MM-DD or null",
  "time_of_day": "morning | afternoon | evening | night | null"
}}

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

5) OUTPUT:
- JSON ONLY.
"""


# ---------------------
# API: Analyze Intent
# ---------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def analyze_intent(request):

    user_message = request.data.get("message", "")
    if not user_message:
        return Response({"error": "message is required"}, status=400)

    try:
        logger.debug(f"[Chatbot] Analyze Intent: {user_message}")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[INTENT_PROMPT, f"User: {user_message}"]
        )

        raw_text = response.text.strip()
        logger.debug(f"[Gemini Raw] {raw_text}")

        # CASE 1: Not English
        if "Your question must be in English" in raw_text:
            return Response(
                {"error": "Your question must be in English and related to weather, which is the domain I can work with!"},
                status=400
            )

        # Parse JSON
        try:
            result = json.loads(raw_text)
        except:
            match = re.search(r"\{[\s\S]+\}", raw_text)
            if not match:
                return Response({"error": "Invalid LLM output", "raw": raw_text}, status=500)
            result = json.loads(match.group())

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
        disaster_keywords = [
            "typhoon", "storm", "super typhoon", "hurricane", "cyclone",
            "flood", "tsunami", "tornado", "earthquake",
            "wildfire", "thunderstorm", "landslide",
            "extreme weather", "natural disaster", "disaster"
        ]

        msg_lower = user_message.lower()
        intents = result.get("intent", [])

        if any(keyword in msg_lower for keyword in disaster_keywords):
            if "disaster" not in intents:
                intents.append("disaster")

        result["intent"] = intents
        
                # ------------------------------------------
        # 3.1 FIX QUAN TRỌNG: ĐÚNG NGÀY "TODAY"
        # ------------------------------------------
        today_keywords = [
            "today", "right now", "this day", "currently",
            "at the moment", "nowadays", "current day"
        ]

        system_today = datetime.utcnow().date()  # ngày hệ thống thực

        if any(k in msg_lower for k in today_keywords):

            # → BỎ LUÔN NGÀY GEMINI, SET LẠI 100%
            result["day"] = system_today.strftime("%Y-%m-%d")

            # ép intent (y hệt tomorrow)
            if "weather_forecast" not in intents:
                intents.append("weather_forecast")
            if "weather_overview" not in intents:
                intents.append("weather_overview")

            result["intent"] = intents

         # ------------------------------------------
        # 3. FIX QUAN TRỌNG: ĐÚNG NGÀY "TOMORROW"
        # ------------------------------------------
        tomorrow_keywords = [
            "tomorrow", "tommorow", "tommorrow", 
            "tmrw", "tomo", "next day", 
            "the next day", "the day after today"
        ]

        today = datetime.utcnow().date()  # ngày hệ thống thực
        system_tomorrow = today + timedelta(days=1)

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

        logger.debug(f"[Final Parsed Intent] {result}")
        return Response(result, status=200)

    except Exception as e:
        logger.error(f"Chatbot intent error: {e}", exc_info=True)
        return Response({"error": str(e)}, status=500)