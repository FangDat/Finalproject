import requests
import datetime
from urllib.parse import quote
import logging
import re
from pprint import pprint
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
import unicodedata
from rapidfuzz import fuzz, process
# Thêm import cache
from django.core.cache import cache

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import os, json

# --- Đọc file ISO codes một lần khi server start ---
ISO_CODES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "iso_codes.json")
try:
    with open(ISO_CODES_PATH, "r", encoding="utf-8") as f:
        ISO_CODES = json.load(f)
        logger.info("✅ ISO_3166-2 loaded successfully (%d countries)", len(ISO_CODES))
except Exception as e:
    ISO_CODES = {}
    logger.warning("⚠️ Không load được ISO_3166-2: %s", e)

# --- Đọc dữ liệu worldcities.json khi server start ---
CITIES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "worldcities.json")
try:
    with open(CITIES_PATH, "r", encoding="utf-8") as f:
        WORLD_CITIES = json.load(f)
        logger.info("✅ WorldCities loaded successfully (%d cities)", len(WORLD_CITIES))
except Exception as e:
    WORLD_CITIES = []
    logger.warning("⚠️ Không load được worldcities.json: %s", e)

# ---------------------------
# Helpers / Weather / Autocomplete
# ---------------------------
def normalize_text(text):
    """Bỏ dấu và chuẩn hóa chữ thường"""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()


def fuzzy_search_cities(query, limit=8):
    """Fuzzy search có fallback admin_name + cache, loại bỏ trùng city/admin_name."""
    query_norm = normalize_text(query)
    if not query_norm:
        return []
    
    if len(query_norm) > 15 and sum(ch in "aeiou" for ch in query_norm) < 2:
        return []

    cache_key = f"fuzzy_local:{query_norm}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"✅ [CACHE HIT] fuzzy search: {query}")
        return cached

    matches = []
    seen = set()  # tránh trùng lặp cùng cặp city|admin

    for city in WORLD_CITIES:
        city_name = city.get("city", "") or ""
        city_ascii = city.get("city_ascii", "") or ""
        admin_name = city.get("admin_name", "") or ""

        # Nếu city và admin giống nhau => coi như không có admin (để tránh "Quảng Nam, Quảng Nam")
        if normalize_text(city_name) == normalize_text(admin_name):
            admin_name_to_use = ""
        else:
            admin_name_to_use = admin_name

        city_norm = normalize_text(city_ascii)
        admin_norm = normalize_text(admin_name_to_use)
        name_norm = normalize_text(city_name)

        # Score: ưu tiên so với city_ascii, nhưng cũng so với admin
        score_city = fuzz.token_set_ratio(query_norm, city_norm)
        score_admin = fuzz.token_set_ratio(query_norm, admin_norm)

        # Nếu query trùng 100% với city_ascii hoặc với city có dấu, cho điểm cực lớn để đứng đầu
        if query_norm == city_norm or query_norm == name_norm:
            score_city = 1000

        best_score = max(score_city, score_admin)
        if best_score > 60:  # ngưỡng có thể điều chỉnh
            key = f"{normalize_text(city_name)}|{normalize_text(admin_name_to_use)}"
            if key not in seen:
                seen.add(key)
                matches.append({
                    "city": city_name,
                    "admin_name": admin_name_to_use,
                    "lat": city.get("lat"),
                    "lon": city.get("lng"),   # dùng 'lon' cho nhất quán
                    "score": best_score,
                })
    if not matches:
        logger.debug(f"❌ No fuzzy matches for '{query}'")
        return []
    
    # Sort theo score giảm dần, sau đó lấy limit
    matches.sort(key=lambda x: -x["score"])
    results = matches[:limit]
    
    max_score = results[0]["score"]
    SCORE_THRESHOLD = 80  # bạn có thể chỉnh lên/xuống tùy độ khắt khe
    if max_score < SCORE_THRESHOLD:
        logger.debug(f"⚠️ Fuzzy top score {max_score} < {SCORE_THRESHOLD} → coi như không hợp lệ")
        return []

    try:
        cache.set(cache_key, results, timeout=900)
        logger.debug(f"🔁 [CACHE SET] fuzzy search saved key={cache_key}")
    except Exception:
        logger.exception("⚠️ Không lưu được fuzzy search cache")

    return results


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

def normalize_with_iso(comps, display):
    """
    Chuẩn hoá tên địa phương dựa trên mã ISO_3166-2 (ví dụ: 'VN-DN' → 'Đà Nẵng').
    Cấu trúc file ISO_CODES:
    {
        "VN": {
            "name": "Viet Nam",
            "sub": {
                "VN-DN": { "type": "Municipality", "name": "Đà Nẵng" },
                ...
            }
        }
    }
    """
    try:
        iso_field = comps.get("ISO_3166-2") or comps.get("iso_3166_2")
        if not iso_field:
            return display

        iso_codes = iso_field if isinstance(iso_field, list) else [iso_field]

        for code in iso_codes:
            code = code.strip().upper()
            # ví dụ: 'VN-DN' → country_code='VN'
            country_code = code.split("-")[0]

            # Kiểm tra trong cấu trúc ISO_CODES["VN"]["sub"]
            if country_code in ISO_CODES:
                country_data = ISO_CODES[country_code]
                sub = country_data.get("sub", {})
                if code in sub:
                    entry = sub[code]
                    if isinstance(entry, dict) and "name" in entry:
                        fixed_name = entry["name"]
                        logger.info(f"[ISO FIX] {display} → {fixed_name}")
                        return fixed_name

        # fallback giữ nguyên nếu không tìm thấy
        return display

    except Exception as e:
        logger.exception("normalize_with_iso failed: %s", e)
        return display


@api_view(['GET'])
def autocomplete_local(request):
    """
    Autocomplete nội bộ dựa vào worldcities.json (fuzzy search)
    Trả về: name (display), lat, lon, score.
    """
    q = request.GET.get("q") or request.GET.get("query") or ""
    q = q.strip()
    if not q:
        return Response([], status=200)

    logger.debug(f"🔍 Fuzzy search local query='{q}'")

    try:
        results = fuzzy_search_cities(q)

        formatted = []
        seen_names = set()  # tránh hiển thị trùng

        for r in results:
            city = r.get("city", "")
            admin = r.get("admin_name", "")

            # Nếu có admin khác city -> hiển thị "City, Admin"
            if admin and normalize_text(admin) != normalize_text(city):
                display_name = f"{city}, {admin}"
            else:
                display_name = city

            # tránh lặp hiển thị (vd: nhiều bản ghi khác nhau cùng display_name)
            key = display_name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            formatted.append({
                "name": display_name,
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "score": r.get("score")
            })

        return Response(formatted, status=200)
    except Exception as e:
        logger.exception("autocomplete_local failed")
        return Response({"error": str(e)}, status=500)

def get_city_from_coordinates(lat, lon, geocode_key):
    """Reverse geocoding → Từ lat/lon trả về tên thành phố chuẩn hóa (ISO-3166-2)."""
    cache_key = f"geocode:reverse:{lat}:{lon}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"[CACHE HIT] Reverse geocode {lat},{lon} -> {cached}")
        return cached

    try:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={geocode_key}&language=vi"
        geo_resp = requests.get(url, timeout=5).json()
        
        # ✅ In ra để kiểm tra cấu trúc components
        if geo_resp.get("results"):
            pprint(geo_resp["results"][0]["components"])
            print("----------")    
        
    except Exception as e:
        logger.exception(f"Lỗi khi gọi OpenCage reverse geocode: {e}")
        return "Unknown"

    if geo_resp.get("results"):
        for r in geo_resp["results"]:
            comps = r.get("components", {})
            display = build_display_name(comps, r.get("formatted"))

            if display:
                # ✅ Áp dụng chuẩn hóa ISO
                normalized = normalize_with_iso(comps, display)
                result = strip_country_suffix(normalized)

                logger.debug(f"[ISO FIX] {display} → {result}")

                try:
                    cache.set(cache_key, result, timeout=900)
                except Exception:
                    logger.exception("Không lưu reverse geocode vào cache")
                return result

        # fallback nếu không có kết quả nào phù hợp
        raw_display = geo_resp["results"][0].get("formatted")
        result = strip_country_suffix(raw_display)
        cache.set(cache_key, result, timeout=900)
        return result

    return "Unknown"

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

        # --- TRƯỜNG HỢP 1: Người dùng F5 / cho phép định vị ---
        if lat and lon:
            if name:
                city_name = name
                logger.debug("📍 Lấy city_name từ query param name='%s'", name)
            else:
                city_name = get_city_from_coordinates(lat, lon, geocode_key)
                logger.debug("📍 Lấy city_name từ OpenCage reverse geocode: %s", city_name)

            city_name = strip_country_suffix(city_name)

        # --- TRƯỜNG HỢP 2: Người dùng nhập tên thành phố và nhấn Enter ---
        elif city_input:
            logger.debug("🔍 Dùng fuzzy search nội bộ cho city_input='%s'", city_input)
            matches = fuzzy_search_cities(city_input)
            if not matches:
                return Response({"error": f"Không tìm thấy địa điểm '{city_input}'"}, status=404)

            top = matches[0]
            lat = top.get("lat")
            lon = top.get("lon")

            # --- XÂY display_name giống dropdown: nếu có admin khác city -> "City, Admin" ---
            if top.get("admin_name") and normalize_text(top.get("admin_name")) != normalize_text(top.get("city")):
                city_name = f"{top.get('city')}, {top.get('admin_name')}"
            else:
                city_name = top.get("city") or city_input

            logger.debug("✅ Fuzzy top result: %s (%s,%s) score=%s", city_name, lat, lon, top.get("score"))

        else:
            return Response({"error": "Thiếu tham số city hoặc lat/lon"}, status=400)

        # Chuẩn hoá hiển thị
        fixed_name = strip_country_suffix(city_name)

        # Kiểm tra tọa độ
        if not lat or not lon:
            return Response({"error": "Không lấy được tọa độ"}, status=400)


        # --- TẠO CACHE KEY ---
        try:
            lat_s = f"{float(lat):.6f}"
            lon_s = f"{float(lon):.6f}"
        except Exception:
            lat_s = str(lat)
            lon_s = str(lon)

        weather_cache_key = f"weather:{lat_s}:{lon_s}"

        # --- CACHE HIT ---
        cached_weather = cache.get(weather_cache_key)
        if cached_weather:
            logger.info(f"💾 [CACHE HIT] Trả dữ liệu từ Redis cho {weather_cache_key}")
            return Response(cached_weather)
        else:
            logger.info(f"🌍 [API CALL] Gọi OpenWeather cho {weather_cache_key}")

        # --- GỌI OPENWEATHER ---
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        current_resp = requests.get(current_url, timeout=8)
        current_data = current_resp.json()
        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)

        visibility = current_data.get('visibility', None)
        rainfall = current_data.get("rain", {}).get("1h") if isinstance(current_data.get("rain"), dict) else None

        # --- UV INDEX ---
        uv_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,daily,alerts&appid={api_key}"
        uv_resp = requests.get(uv_url, timeout=8)
        uv_data = uv_resp.json()
        uv_index = uv_data.get("current", {}).get("uvi", None)

        # --- TIMEZONE ---
        timezone_offset = current_data.get("timezone", 0)
        offset = datetime.timedelta(seconds=timezone_offset)
        tz = datetime.timezone(offset)
        now = datetime.datetime.now(tz)

        # --- FORECAST ---
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        forecast_resp = requests.get(forecast_url, timeout=8)
        forecast_data = forecast_resp.json()
        if forecast_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu forecast", "details": forecast_data}, status=400)

        upcoming_hours, daily_forecast = [], {}
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)

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

        # --- CHANCE OF RAIN ---
        chance_of_rain = 0
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                chance_of_rain = item.get("pop", 0) * 100
                break

        # --- DAILY FORECAST LIST ---
        daily_forecast_list = []
        for day, info in list(daily_forecast.items())[:3]:
            most_common_icon = choose_daytime_icon(info.get("icons", []))
            daily_forecast_list.append({
                "day": day,
                "temp": f"{int(max(info['temps']))}/{int(min(info['temps']))}",
                "icon": most_common_icon
            })

        result = {
            "location": fixed_name,
            "temperature": current_data['main']['temp'],
            "humidity": current_data['main']['humidity'],
            "condition": current_data['weather'][0]['main'].lower(),
            "icon": current_data['weather'][0]['icon'],
            "wind_speed": current_data['wind']['speed'],
            "chance_of_rain": round(chance_of_rain),
            "upcoming_hours": upcoming_hours,
            "daily_forecast": daily_forecast_list,
            "visibility": visibility,
            "uv_index": uv_index,
            "rainfall": rainfall,
            "source": "OpenWeather"
        }

        # Thêm toạ độ nếu có
        if lat and lon:
            result["lat"] = float(lat)
            result["lon"] = float(lon)
            result["fixed_name"] = fixed_name

        # --- LƯU CACHE ---
        try:
            cache.set(weather_cache_key, result, timeout=900)
            logger.debug("🔁 Lưu weather vào Redis cache key=%s", weather_cache_key)
        except Exception:
            logger.exception("Không lưu được weather vào cache")

        return Response(result)

    except Exception as e:
        logger.exception("get_weather failed")
        return Response({"error": str(e)}, status=500)
