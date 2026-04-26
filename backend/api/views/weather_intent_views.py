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
# LOGGER (DEBUG → checkjson.log)
# -------------------------------
logger = logging.getLogger(__name__)

# -------------------------------
# CONFIG
# -------------------------------
OPENWEATHER_API_KEY = settings.OPENWEATHER_API_KEY
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

    local_tz = timezone(timedelta(seconds=tz_offset_seconds))   # Create timezone
    dt = datetime.fromtimestamp(ts, tz=local_tz)     # Convert timestamp
    return dt.strftime("%Y-%m-%d %H:%M:%S") # Format datetime string


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

def map_aqi_level(aqi):
    """
    Convert OpenWeather AQI (1–5) → human readable
    """
    return {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor",
    }.get(aqi, "Unknown")


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

def normalize_air_pollution(item, tz_offset):
    """
    Normalize OpenWeather air pollution forecast item
    """
    return {
        "time": unix_to_local(item.get("dt"), tz_offset),
        "air_quality": {
            "aqi": item.get("main", {}).get("aqi"),
            "level": map_aqi_level(
                item.get("main", {}).get("aqi")
            ),
        },
        "components (μg/m3)": {
            "co": item.get("components", {}).get("co"),
            "so2": item.get("components", {}).get("so2"),
            "pm10": item.get("components", {}).get("pm10"),
        },
    }




# -------------------------------
# CORE: ROUTER BY INTENT
# -------------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def weather_by_intent(request):  # Main function to handle intent-based weather requests
    """
    Input: intent JSON from /api/chatbot/intent/
    Output: weather data
    """

    # ⚠️ DEBUG ONLY: clear log mỗi request
    if settings.DEBUG:
        open(settings.DEBUG_INTENT_LOG_FILE, "w").close()
        logger.debug("===== NEW WEATHER INTENT REQUEST =====")

    intent_payload = request.data   # Get JSON data from request body

    if settings.DEBUG:
        logger.debug("INTENT INPUT")
        logger.debug(json.dumps(intent_payload, indent=2, ensure_ascii=False))

    location = intent_payload.get("location")   # Extract location from input
    day = intent_payload.get("day") # Extract day (if provided)
    intents = intent_payload.get("intent", [])   # Extract intent list (default empty)

    # -------------------------------
    # Resolve lat/lon
    # -------------------------------
    matches = fuzzy_search_cities(location)  # Find matching cities using fuzzy search
    if not matches:  # If no location match found
        if settings.DEBUG:
            logger.debug("LOCATION NOT FOUND")
        return Response({"error": "Location not found"}, status=404)

    city = matches[0]   # Take best match result
    lat, lon = city["lat"], city["lon"]  # Extract latitude and longitude

    if settings.DEBUG:
        logger.debug("RESOLVED LOCATION")
        logger.debug(json.dumps(city, indent=2, ensure_ascii=False))

    responses = {}  # Initialize response container

    for tool_name in intents:   # Loop through requested intent tools
    # -------------------------------
    # DAILY AGGREGATION
    # -------------------------------
        if tool_name == "daily_aggregation" and day:     # Check if intent is daily summary
            if settings.DEBUG:
                logger.debug("CALLING DAY SUMMARY API")

            r = requests.get(
                f"{BASE_OW_URL}/onecall/day_summary",
                params={
                    "lat": lat,
                    "lon": lon,
                    "date": day,
                    "appid": OPENWEATHER_API_KEY,
                },
                timeout=8,
            )

            raw_data = r.json() # Parse API response JSON
            normalized_daily = normalize_daily_aggregation(raw_data)     # Normalize data
            responses['daily_aggregation'] = normalized_daily    # Store result

            if settings.DEBUG:
                logger.debug("DAY SUMMARY NORMALIZED (LLM READY)")
                logger.debug(json.dumps(normalized_daily, indent=2, ensure_ascii=False))


        # -------------------------------
        # WEATHER OVERVIEW
        # -------------------------------
        elif tool_name == "weather_overview":    # Check overview intent
            r = requests.get(
                f"{BASE_OW_URL}/onecall/overview",   # Endpoint URL
                params={
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "appid": OPENWEATHER_API_KEY,
                },
                timeout=8,
            )

            data = r.json() # Parse JSON response
            responses["weather_overview"] = data    # Store overview data

            if settings.DEBUG:
                logger.debug("WEATHER OVERVIEW RESPONSE")
                logger.debug(json.dumps(data, indent=2, ensure_ascii=False))

        # -------------------------------
        # WEATHER FORECAST
        # -------------------------------
        elif tool_name == "weather_forecast":
            r = requests.get(
                f"{BASE_OW_URL}/onecall",
                params={
                    "lat": lat,
                    "lon": lon,
                    "exclude": "minutely,alerts",
                    "appid": OPENWEATHER_API_KEY,
                },
                timeout=8,
            )

            raw_data = r.json()

            tz_offset = raw_data.get("timezone_offset", 0)   # Get timezone offset
            tz_string = f"{tz_offset // 3600:+03d}:00"   # Convert to readable timezone


            # ============================
            # STEP 3 – NORMALIZE DATA
            # ============================
            normalized_data = { # Normalize forecast data
                "tz": tz_string,     # Timezone string
                "current": normalize_hourly(    
                    raw_data.get("current", {}), tz_offset  # Normalize current weather
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

            # 👉 RESPONSE FOR CHATBOT
            responses["weather_forecast"] = normalized_data
            
            # -------------------------------
        # AIR POLLUTION FORECAST
        # -------------------------------
        elif tool_name == "air_pollution":
            if settings.DEBUG:
                logger.debug("CALLING AIR POLLUTION FORECAST API")

            r = requests.get(
                "https://api.openweathermap.org/data/2.5/air_pollution/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": OPENWEATHER_API_KEY,
                },
                timeout=8,
            )

            raw_data = r.json()

            # timezone offset
            tz_offset = raw_data.get("timezone_offset", 0)   # Get timezone offset
            tz_string = f"{tz_offset // 3600:+03d}:00" # Format timezone

           
            if "weather_forecast" in responses:  # If forecast already exists
                tz_string = responses["weather_forecast"].get("tz", "+00:00")   # Reuse timezone
                try:
                    tz_offset = int(tz_string.split(":")[0]) * 3600 # Convert to seconds
                except:
                    tz_offset = 0

            normalized_air = [  # Normalize air data list
                normalize_air_pollution(item, tz_offset)
                for item in raw_data.get("list", [])
            ]

            responses["air_pollution"] = {
                "coord": raw_data.get("coord"),
                "forecast": normalized_air,
            }

            if settings.DEBUG:
                logger.debug("AIR POLLUTION NORMALIZED RESPONSE (LLM READY)")
                logger.debug(
                    json.dumps(
                        responses["air_pollution"],
                        indent=2,
                        ensure_ascii=False,
                    )
                )


        # -------------------------------
        # ACTIVITY / DISASTER → LLM LATER (RAM ONLY)
        # -------------------------------
        elif tool_name == "activity_recommendation" or tool_name == "disaster" or tool_name == "heathcare":
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
