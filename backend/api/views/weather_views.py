import requests
import datetime
from urllib.parse import quote
import logging
import re
from collections import Counter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------
# Helpers / Weather / Autocomplete
# ---------------------------


def strip_country_suffix(formatted):
    if not formatted:
        return formatted
    parts = formatted.split(',')
    if parts and parts[-1].strip().lower() in ("vietnam", "việt nam", "vn"):
        parts = parts[:-1]
    return ", ".join([p.strip() for p in parts])


def clean_city_name(raw_name):
    if not raw_name:
        return None
    raw = str(raw_name).strip()
    prefixes = ["Thành phố ", "Tp. ", "Tp ", "TP. ", "TP ", "Tỉnh ", "Thủ đô "]
    for p in prefixes:
        if raw.startswith(p):
            raw = raw[len(p):].strip()
    return raw


def build_display_name(comps, fallback):
    district = comps.get("suburb") or comps.get(
        "city_district") or comps.get("county")
    city = comps.get("city") or comps.get("town")
    state = comps.get("state") or comps.get("province")

    if district and city:
        return f"{clean_city_name(district)}, {clean_city_name(city)}"
    if district and state:
        return f"{clean_city_name(district)}, {clean_city_name(state)}"
    if city and state:
        return f"{clean_city_name(city)}, {clean_city_name(state)}"
    return clean_city_name(fallback)


@api_view(['GET'])
def autocomplete(request):
    geocode_key = "c173e9b1e4c14ee3845dfa894f82a9c7"
    q = request.GET.get("q") or request.GET.get("query") or ""
    q = q.strip()
    if not q:
        return Response([], status=200)

    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={quote(q)}&key={geocode_key}&language=vi&limit=10"
        resp = requests.get(url, timeout=8)
        geo = resp.json()
    except Exception as e:
        return Response({"error": "Geocode failed", "details": str(e)}, status=500)

    results = geo.get("results", [])
    suggestions = []

    def score_result(r):
        comps = r.get("components", {})
        score = 0
        if comps.get("country_code", "").lower() == "vn":
            score += 10
        main_keys = ["city", "town", "village", "municipality",
                     "county", "state", "province", "region"]
        lower_q = q.lower()
        for k in main_keys:
            v = comps.get(k)
            if v and lower_q in str(v).lower():
                score += 5
        return score

    def get_place_rank(comps):
        if comps.get("city") or comps.get("town"):
            return 2
        if comps.get("county") or comps.get("city_district") or comps.get("district"):
            return 3
        if comps.get("suburb") or comps.get("village") or comps.get("ward"):
            return 4
        return 5

    exact_matches = []
    scored = []

    for r in results:
        geometry = r.get("geometry", {})
        comps = r.get("components", {})
        display = build_display_name(comps, r.get("formatted"))
        display = strip_country_suffix(display)
        if display and display.lower() == q.lower():
            exact_matches.append({
                "name": display,
                "lat": geometry.get("lat"),
                "lon": geometry.get("lng"),
                "is_vn": (comps.get("country_code", "").lower() == "vn"),
                "raw": r.get("formatted", "")
            })
        else:
            rank = get_place_rank(comps)
            scored.append((rank, score_result(r), {
                "name": display,
                "lat": geometry.get("lat"),
                "lon": geometry.get("lng"),
                "is_vn": (comps.get("country_code", "").lower() == "vn"),
                "raw": r.get("formatted", "")
            }))

    scored.sort(key=lambda x: (x[0], -x[1]))
    suggestions = []
    seen = set()

    for item in exact_matches:
        key = item["name"].lower()
        if key not in seen:
            seen.add(key)
            suggestions.append(item)
        if len(suggestions) >= 8:
            break

    for _, _, item in scored:
        if len(suggestions) >= 8:
            break
        key = (item.get("name") or "").lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(item)

    return Response(suggestions)


def get_city_from_coordinates(lat, lon, geocode_key):
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={geocode_key}&language=vi"
    geo_resp = requests.get(geocode_url).json()
    if geo_resp.get("results"):
        for r in geo_resp["results"]:
            comps = r.get("components", {})
            display = build_display_name(comps, r.get("formatted"))
            if display:
                return strip_country_suffix(display)
        return strip_country_suffix(geo_resp["results"][0].get("formatted"))
    return None


# ---------------------------
# Helper chọn icon ban ngày
# ---------------------------
def choose_daytime_icon(icons):
    """
    Chọn icon phổ biến nhất cho ngày.
    Nếu icon phổ biến nhất là ban đêm (01n, 02n, ...), 
    fallback sang icon ban ngày (01d, 02d, ...) gần nhất.
    """
    if not icons:
        return None
    counter = Counter(icons)
    most_common_icon = counter.most_common(1)[0][0]

    # Nếu icon phổ biến nhất là ban đêm
    if most_common_icon.endswith('n'):
        # Tìm icon ban ngày cùng loại
        daytime_icons = [i for i in icons if i.endswith('d')]
        if daytime_icons:
            daytime_counter = Counter(daytime_icons)
            most_common_icon = daytime_counter.most_common(1)[0][0]
    return most_common_icon

# ---------------------------
# GET WEATHER
# ---------------------------
@api_view(['GET'])
def get_weather(request):
    api_key = "49d2545d1cdff8820a039e6e2f451ffc"
    geocode_key = "f70417a9320a42c28e2f87398e996e6f"

    city_input = request.GET.get("city")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    name = request.GET.get("name")

    try:
        city_name = None
        if lat and lon:
            if name:
                city_name = name
            else:
                city_name = get_city_from_coordinates(lat, lon, geocode_key)
            city_name = strip_country_suffix(city_name)
        else:
            if not city_input:
                return Response({"error": "Cần city hoặc lat/lon"}, status=400)
            geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={quote(city_input.strip())}&key={geocode_key}&language=vi&limit=10"
            geo_resp = requests.get(geocode_url).json()
            if not geo_resp.get("results"):
                return Response({"error": f"Không tìm thấy địa điểm '{city_input}'"}, status=404)
            chosen = geo_resp["results"][0]
            geometry = chosen.get("geometry", {})
            lat, lon = geometry.get("lat"), geometry.get("lng")
            comps = chosen.get("components", {})
            city_name = build_display_name(comps, chosen.get("formatted"))
            city_name = strip_country_suffix(city_name)

        if not lat or not lon:
            return Response({"error": "Không lấy được tọa độ cho địa điểm"}, status=400)

        # Current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        current_resp = requests.get(current_url)
        current_data = current_resp.json()
        visibility = current_data.get('visibility', None)
        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)
        
                # --- lấy UV index ---
        uv_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={api_key}"
        uv_resp = requests.get(uv_url, timeout=8)
        uv_data = uv_resp.json()
        uv_index = uv_data.get("current", {}).get("uvi", None)


        timezone_offset = current_data.get("timezone", 0)
        offset = datetime.timedelta(seconds=timezone_offset)
        tz = datetime.timezone(offset)
        now = datetime.datetime.now(tz)

        # Forecast
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        forecast_resp = requests.get(forecast_url)
        forecast_data = forecast_resp.json()
        if forecast_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu forecast", "details": forecast_data}, status=400)

        upcoming_hours, daily_forecast = [], {}
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(
                item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(
                tzinfo=datetime.timezone.utc).astimezone(tz)

            if dt_local > now and len(upcoming_hours) < 5:
                upcoming_hours.append({
                    "time": dt_local.strftime("%Y-%m-%d %H:%M"),
                    "temp": item['main']['temp'],
                    "condition": item['weather'][0]['main'].lower(),
                    "icon": item['weather'][0]['icon']
                })

            day_str = dt_local.date().isoformat()
            if day_str not in daily_forecast:
                daily_forecast[day_str] = {"temps": [], "icons": []}
            daily_forecast[day_str]["temps"].append(item['main']['temp'])
            daily_forecast[day_str]["icons"].append(item['weather'][0]['icon'])

        chance_of_rain = 0
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(
                item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(
                tzinfo=datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                chance_of_rain = item.get("pop", 0) * 100
                break
            
                # Tạo danh sách forecast theo ngày
        daily_forecast_list = []
        for day, info in list(daily_forecast.items())[:3]:
            # Chọn icon xuất hiện nhiều nhất trong ngày, với fallback ban ngày
            most_common_icon = choose_daytime_icon(info.get("icons", []))
            
            daily_forecast_list.append({
                "day": day,
                "temp": f"{int(max(info['temps']))}/{int(min(info['temps']))}",
                "icon": most_common_icon
            })


        result = {
            "location": city_name,
            "temperature": current_data['main']['temp'],
            "humidity": current_data['main']['humidity'],
            "condition": current_data['weather'][0]['main'].lower(),
            "icon": current_data['weather'][0]['icon'],  # ví dụ 01d
            "wind_speed": current_data['wind']['speed'],
            "chance_of_rain": round(chance_of_rain),
            "upcoming_hours": upcoming_hours,
            "daily_forecast": daily_forecast_list,
            "visibility": visibility,
            "uv_index": uv_index,  
            "source": "OpenWeather"
        }
        return Response(result)
    except Exception as e:
        logger.exception("get_weather failed")
        return Response({"error": str(e)}, status=500)
