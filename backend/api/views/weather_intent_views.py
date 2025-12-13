# ================================
# STEP 2 – WEATHER INTENT ROUTER
# File: backend/api/views/weather_intent_views.py
# ================================

import requests
import json
import logging
from datetime import datetime, timezone, timedelta

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .weather_views import fuzzy_search_cities

# -------------------------------
# LOGGER (DEBUG RIÊNG → checkjson.log)
# -------------------------------
logger = logging.getLogger(__name__)

# -------------------------------
# CONFIG
# -------------------------------
OPENWEATHER_KEY = "49d2545d1cdff8820a039e6e2f451ffc"
BASE_OW_URL = "https://api.openweathermap.org/data/3.0"

# ==================================================
# STEP 3 – DATA NORMALIZATION HELPERS
# ==================================================
def unix_to_local(ts, tz_offset_seconds):
    """
    Convert UNIX timestamp → LOCAL datetime string (NO timezone text)
    """
    if not ts:
        return None

    local_tz = timezone(timedelta(seconds=tz_offset_seconds))
    dt = datetime.fromtimestamp(ts, tz=local_tz)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def kelvin_to_celsius(k):
    return round(k - 273.15, 2) if k is not None else None


def format_visibility(m):
    return f"{m/1000:.1f} km" if m is not None else None


def format_humidity(h):
    return f"{h}%" if h is not None else None


def format_clouds(c):
    return f"{c}%" if c is not None else None


def format_wind_speed(w):
    return f"{w}m/s" if w is not None else None

def format_rainfall(mm):
    return f"{mm} mm" if mm is not None else None

def format_pop(pop):
    return f"{int(pop * 100)}%" if pop is not None else None


def normalize_hourly(hour, tz_offset):
    return {
        "time": unix_to_local(hour.get("dt"), tz_offset),
        "temperature °C": kelvin_to_celsius(hour.get("temp")),
        "humidity": format_humidity(hour.get("humidity")),
        "uvi": hour.get("uvi"),
        "clouds": format_clouds(hour.get("clouds")),
        "visibility": format_visibility(hour.get("visibility")),
        "wind_speed": format_wind_speed(hour.get("wind_speed")),
        "weather_condition": hour.get("weather", [{}])[0].get("main"),
        "rain_probability": format_pop(hour.get("pop")),
    }


def normalize_daily(day, tz_offset):
    return {
        "date": unix_to_local(day.get("dt"), tz_offset),
        "sunrise": unix_to_local(day.get("sunrise"), tz_offset),
        "sunset": unix_to_local(day.get("sunset"), tz_offset),
        "moonrise": unix_to_local(day.get("moonrise"), tz_offset),
        "moonset": unix_to_local(day.get("moonset"), tz_offset),
        "summary": day.get("summary"),
        "temperature °C": {
            "day": kelvin_to_celsius(day["temp"].get("day")),
            "min": kelvin_to_celsius(day["temp"].get("min")),
            "max": kelvin_to_celsius(day["temp"].get("max")),
            "evening": kelvin_to_celsius(day["temp"].get("eve")),
            "morning": kelvin_to_celsius(day["temp"].get("morn")),
        },
        "humidity": format_humidity(day.get("humidity")),
       "wind_speed": format_wind_speed(day.get("wind_speed")),
        "weather_condition": day.get("weather", [{}])[0].get("main"),
        "clouds": format_clouds(day.get("clouds")),
        "rain_probability": format_pop(day.get("pop")),
        "rain_mm": day.get("rain"),
        "uvi": day.get("uvi"),
    }
    
def normalize_daily_aggregation(raw):
    """
    Normalize OpenWeather day_summary → LLM-friendly JSON
    """

    tz = raw.get("tz", "+00:00")

    temp = raw.get("temperature", {})
    wind = raw.get("wind", {})
    clouds = raw.get("cloud_cover", {})
    humidity = raw.get("humidity", {})
    precipitation = raw.get("precipitation", {})

    return {
        "tz": tz,
        "date": raw.get("date"),

        "temperature °C": {
            "min": kelvin_to_celsius(temp.get("min")),
            "max": kelvin_to_celsius(temp.get("max")),
            "morning": kelvin_to_celsius(temp.get("morning")),
            "afternoon": kelvin_to_celsius(temp.get("afternoon")),
            "evening": kelvin_to_celsius(temp.get("evening")),
        },

        "humidity": format_humidity(humidity.get("afternoon")),
        "cloud_cover": format_clouds(clouds.get("afternoon")),
         "rainfall": format_rainfall(
            precipitation.get("total")
        ),
        "wind": {
            "speed": format_wind_speed(
                wind.get("max", {}).get("speed")
            )
        }
    }



# -------------------------------
# CORE: ROUTER BY INTENT
# -------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def weather_by_intent(request):
    """
    Input: intent JSON from /api/chatbot/intent/
    Output: weather data (KHÔNG dùng log làm dữ liệu)
    """

    # ⚠️ DEBUG ONLY: clear log mỗi request
    if settings.DEBUG:
        open(settings.DEBUG_INTENT_LOG_FILE, "w").close()
        logger.debug("===== NEW WEATHER INTENT REQUEST =====")

    intent_payload = request.data

    if settings.DEBUG:
        logger.debug("INTENT INPUT")
        logger.debug(json.dumps(intent_payload, indent=2, ensure_ascii=False))

    location = intent_payload.get("location")
    day = intent_payload.get("day")
    intents = intent_payload.get("intent", [])

    # -------------------------------
    # Resolve lat/lon
    # -------------------------------
    matches = fuzzy_search_cities(location)
    if not matches:
        if settings.DEBUG:
            logger.debug("LOCATION NOT FOUND")
        return Response({"error": "Location not found"}, status=404)

    city = matches[0]
    lat, lon = city["lat"], city["lon"]

    if settings.DEBUG:
        logger.debug("RESOLVED LOCATION")
        logger.debug(json.dumps(city, indent=2, ensure_ascii=False))

    responses = {}

    # -------------------------------
    # DAILY AGGREGATION
    # -------------------------------
    if "daily_aggregation" in intents and day:
        if settings.DEBUG:
            logger.debug("CALLING DAY SUMMARY API")

        r = requests.get(
            f"{BASE_OW_URL}/onecall/day_summary",
            params={
                "lat": lat,
                "lon": lon,
                "date": day,
                "appid": OPENWEATHER_KEY,
            },
            timeout=8,
        )

        raw_data = r.json()
        normalized_daily = normalize_daily_aggregation(raw_data)
        responses['daily_aggregation'] = normalized_daily

        if settings.DEBUG:
            logger.debug("DAY SUMMARY NORMALIZED (LLM READY)")
            logger.debug(json.dumps(normalized_daily, indent=2, ensure_ascii=False))


    # -------------------------------
    # WEATHER OVERVIEW
    # -------------------------------
    if "weather_overview" in intents:
        r = requests.get(
            f"{BASE_OW_URL}/onecall/overview",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OPENWEATHER_KEY,
            },
            timeout=8,
        )

        data = r.json()
        responses["weather_overview"] = data

        if settings.DEBUG:
            logger.debug("WEATHER OVERVIEW RESPONSE")
            logger.debug(json.dumps(data, indent=2, ensure_ascii=False))

    # -------------------------------
    # WEATHER FORECAST
    # -------------------------------
    if "weather_forecast" in intents:
        r = requests.get(
            f"{BASE_OW_URL}/onecall",
            params={
                "lat": lat,
                "lon": lon,
                "exclude": "minutely,alerts",
                "appid": OPENWEATHER_KEY,
            },
            timeout=8,
        )

        raw_data = r.json()

        tz_offset = raw_data.get("timezone_offset", 0)
        tz_string = f"{tz_offset // 3600:+03d}:00"

        # # ============================
        # # DEBUG – GIỮ NGUYÊN RAW JSON
        # # ============================
        # if settings.DEBUG:
        #     logger.debug("WEATHER FORECAST RAW RESPONSE (OPENWEATHER)")
        #     logger.debug(json.dumps(raw_data, indent=2, ensure_ascii=False))

        # ============================
        # STEP 3 – NORMALIZE DATA
        # ============================
        normalized_data = {
            "tz": tz_string,
            "current": normalize_hourly(
                raw_data.get("current", {}), tz_offset
            ),
            "hourly": [
                normalize_hourly(h, tz_offset)
                for h in raw_data.get("hourly", [])
            ],
            "daily": [
                normalize_daily(d, tz_offset)
                for d in raw_data.get("daily", [])
            ],
        }

        # ============================
        # DEBUG – NORMALIZED JSON
        # ============================
        if settings.DEBUG:
            logger.debug(
                "WEATHER FORECAST NORMALIZED RESPONSE (LLM READY)"
            )
            logger.debug(
                json.dumps(normalized_data, indent=2, ensure_ascii=False)
            )

        # 👉 RESPONSE CHO CHATBOT
        responses["weather_forecast"] = normalized_data

    # -------------------------------
    # ACTIVITY / DISASTER → LLM LATER (RAM ONLY)
    # -------------------------------
    if "activity_recommendation" in intents or "disaster" in intents:
        responses["llm_required"] = True

        if settings.DEBUG:
            logger.debug("LLM_REASONING_REQUIRED (NOT USING LOG FILE)")
            logger.debug(
                json.dumps(
                    {
                        "intents": intents,
                        "location": location,
                        "day": day,
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )

    # -------------------------------
    # FINAL RESPONSE
    # -------------------------------
    response_payload = {
        # 'location': location,
        # 'lat': lat,
        # 'lon': lon,
        # 'intents': intents,
        "data": responses,
    }

    return Response(response_payload)
