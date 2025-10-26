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
def autocomplete(request):
    """
    Autocomplete khi người dùng search → KHÔNG ÁP DỤNG ISO_3166-2.
    """
    geocode_key = "f70417a9320a42c28e2f87398e996e6f"
    q = request.GET.get("q") or request.GET.get("query") or ""
    q = q.strip()
    if not q:
        return Response([], status=200)

    cache_key = f"geocode:autocomplete:{q.lower()}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug("✅ Autocomplete: trả về từ Redis cache cho query=%s", q)
        return Response(cached, status=200)

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
        # ✅ KHÔNG normalize_with_iso trong autocomplete
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

    # Cache 15 phút
    try:
        cache.set(cache_key, suggestions, timeout=900)
        logger.debug("🔁 Autocomplete: lưu vào Redis cache key=%s", cache_key)
    except Exception:
        logger.exception("Không lưu được autocomplete vào cache")

    return Response(suggestions)


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
        # Nếu client gửi lat/lon -> dùng lat/lon trực tiếp (cache key dựa trên lat:lon)
        if lat and lon:
            if name:
                city_name = name
            else:
                city_name = get_city_from_coordinates(lat, lon, geocode_key)
            city_name = strip_country_suffix(city_name)
        else:
            if not city_input:
                return Response({"error": "Cần city hoặc lat/lon"}, status=400)

            # Trước khi gọi geocode, check cache geocode query (city_input)
            geocode_cache_key = f"geocode:query:{city_input.strip().lower()}"
            geo_resp_cached = cache.get(geocode_cache_key)
            if geo_resp_cached:
                chosen = geo_resp_cached
                logger.debug("✅ Geocode query trả về từ cache cho '%s'", city_input)
            else:
                geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={quote(city_input.strip())}&key={geocode_key}&language=vi&limit=10"
                geocode_resp = requests.get(geocode_url, timeout=8)
                geocode_json = geocode_resp.json()
                if not geocode_json.get("results"):
                    return Response({"error": f"Không tìm thấy địa điểm '{city_input}'"}, status=404)
                chosen = geocode_json["results"][0]
                # Lưu kết quả geocode (chọn kết quả đầu) vào cache 15 phút
                try:
                    cache.set(geocode_cache_key, chosen, timeout=900)
                    logger.debug("🔁 Lưu geocode query vào cache key=%s", geocode_cache_key)
                except Exception:
                    logger.exception("Không lưu geocode query vào cache")

            geometry = chosen.get("geometry", {})
            lat, lon = geometry.get("lat"), geometry.get("lng")
            comps = chosen.get("components", {})
            city_name = build_display_name(comps, chosen.get("formatted"))
            city_name = strip_country_suffix(city_name)

        if not lat or not lon:
            return Response({"error": "Không lấy được tọa độ cho địa điểm"}, status=400)

        # Tạo cache key cho weather dựa trên lat:lon (chuẩn hóa string)
        # Dùng 6 chữ số thập phân để tránh khác biệt float không đáng có
        try:
            lat_s = f"{float(lat):.6f}"
            lon_s = f"{float(lon):.6f}"
        except Exception:
            lat_s = str(lat)
            lon_s = str(lon)
        weather_cache_key = f"weather:{lat_s}:{lon_s}"

        # Nếu có trong cache -> trả luôn
        cached_weather = cache.get(weather_cache_key)
        if cached_weather:
            logger.info(f"💾 [CACHE HIT] Trả dữ liệu từ Redis cho key={weather_cache_key}")
            logger.debug("✅ Trả weather từ Redis cache cho key=%s", weather_cache_key)
            return Response(cached_weather)
        else:
            logger.info(f"🌍 [API CALL] Gọi OpenWeather cho key={weather_cache_key}")

        # --- gọi API OpenWeather ---
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        current_resp = requests.get(current_url, timeout=8)
        current_data = current_resp.json()
        visibility = current_data.get('visibility', None)
        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)
        
        rainfall = None
        if "rain" in current_data and isinstance(current_data["rain"], dict):
            rainfall = current_data["rain"].get("1h")
        
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
        forecast_resp = requests.get(forecast_url, timeout=8)
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
            "rainfall": rainfall,
            "source": "OpenWeather"
        }

        # Lưu kết quả weather vào cache 15 phút
        try:
            cache.set(weather_cache_key, result, timeout=900)
            logger.debug("🔁 Lưu weather vào Redis cache key=%s", weather_cache_key)
        except Exception:
            logger.exception("Không lưu được weather vào cache")

        return Response(result)
    except Exception as e:
        logger.exception("get_weather failed")
        return Response({"error": str(e)}, status=500)
