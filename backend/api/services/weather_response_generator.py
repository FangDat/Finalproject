# backend/api/services/weather_response_generator.py

import json
import logging
from google import genai

logger = logging.getLogger(__name__)

# ============================
# INIT GEMINI CLIENT (REUSE KEY)
# ============================
GEMINI_API_KEY = "AIzaSyBIMxmqjk-9sb7LPnB95kvbBXKnQcLkCkI"
client = genai.Client(api_key=GEMINI_API_KEY)

#AIzaSyBIMxmqjk-9sb7LPnB95kvbBXKnQcLkCkI
#AIzaSyDF8L7KU3jhUfCxD3PU6EVavb7afcUrLtI
#AIzaSyC_nvEv1gM5SjwJT5D3EYb1RqMGQz-fCWA


# ============================
# PROMPT – LLM RESPONSE GENERATOR
# ============================
WEATHER_RESPONSE_PROMPT = """
You are VietCloud, a professional weather assistant.

You will receive:
1) The original user question
2) Intent analysis
3) Cleaned weather data from OpenWeather

Your task:
- Answer the user naturally and concisely in English.
- Use ONLY the provided data.
- DO NOT invent values.

IMPORTANT RULES:

1) DATE & TIME AWARENESS
- Read the exact date from the data.
- Answer ONLY for that date and time_of_day.
- Never confuse today, tomorrow, or other days.

2) QUESTION TYPE
- If the question is YES/NO → answer directly.
- If general → give a short overview.
- Stay strictly on topic.

3) BASIC WEATHER ANSWERS
Mention only what is relevant:
- temperature
- rain probability or rainfall
- cloud cover
- visibility (if available)
- wind (only if notable)

4) ACTIVITY_RECOMMENDATION
If intent includes "activity_recommendation":
- Assess suitability briefly (good / acceptable / not ideal).
- Explain using weather evidence.
- Add this sentence at the end:
  "VietCloud’s advice is based on forecast data and may not be fully accurate."

5) DISASTER
If intent includes "disaster":
- Be calm and factual.
- If no abnormal signs, say so clearly.
- Example: no signs of earthquakes or extreme weather.
- Add this sentence at the end:
  "VietCloud’s advice is based on forecast data and may not be fully accurate."

6) STYLE
- 30–40 words
- Professional, neutral, friendly
- No emojis
- No bullet points

Output ONLY the final answer text.
"""


# ============================
# CORE FUNCTION
# ============================
def generate_weather_response(
    user_question: str,
    intent_result: dict,
    weather_data: dict
):
    """
    LLM #2 – Generate final natural language answer
    """

    payload = {
        "user_question": user_question,
        "intent_result": intent_result,
        "weather_data": weather_data
    }

    logger.debug("LLM RESPONSE INPUT")
    logger.debug(json.dumps(payload, indent=2, ensure_ascii=False))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            WEATHER_RESPONSE_PROMPT,
            json.dumps(payload, ensure_ascii=False)
        ]
    )

    answer = response.text.strip()

    logger.debug("LLM RESPONSE OUTPUT")
    logger.debug(answer)

    return answer
