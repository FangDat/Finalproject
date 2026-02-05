# backend/api/services/weather_response_generator.py

import json
import logging
from openai import OpenAI
import os
logger = logging.getLogger(__name__)

# ============================
# INIT OPENAI CLIENT
# ============================
# ============================
# INIT OPENAI CLIENT (ENV)
# ============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.error("❌ OPENAI_API_KEY is missing in environment variables")
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)


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
- visibility (if available)
- wind (only if notable)
- air pollution(only if notable)

4) ACTIVITY_RECOMMENDATION
If intent includes "activity_recommendation":
- Assess suitability briefly (good / acceptable / not ideal).
- Decide activity type:
  • Outdoor → if dry weather and mild temperature
  • Indoor → if too much hot hot, rain, cold, or uncomfortable conditions
  
- You MAY suggest 2–3 WELL-KNOWN tourist places
  that logically match the activity type AND the detected location.
  (Example: Hoan Kiem Lake, Temple of Literature, museums, shopping centers.)

- Place names must be real and commonly known.
- Do NOT invent weather values.
- Do NOT invent fictional places.
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
  
6) HEALTHCARE
If intent includes "healthcare":
- Give GENERAL, NON-DIAGNOSTIC advice only.
- Base suggestions on:
  • reported symptoms
  • current weather conditions
- DO NOT provide medical diagnosis.
- DO NOT prescribe medication.
- Suggestions may include:
  • rest, hydration if needed
  • avoiding extreme weather exposure
  • appropriate clothing
  • wear masks if air pollution is high
- Always end with this sentence EXACTLY:
  "If your health condition worsens, we recommend visiting the nearest medical facility for appropriate treatment."

7) STYLE
- 36–63 words
- Professional, neutral, friendly
- Comfortable emojis
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

    response = client.responses.create(
        model="gpt-4o",  # GPT-4.0 (OpenAI standard)
        input=[
            {
                "role": "system",
                "content": WEATHER_RESPONSE_PROMPT
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False)
            }
        ],
    )

    answer = response.output_text.strip()

    logger.debug("LLM RESPONSE OUTPUT")
    logger.debug(answer)

    return answer
