import requests
import datetime
from urllib.parse import quote
import logging
import re
from bson import ObjectId
from django.utils import timezone
from ..models import SearchHistory, User
from rest_framework.permissions import IsAuthenticated
from backend.api.permissions.is_premium_user import IsPremiumUser
from django.core.cache import cache
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

from django.conf import settings

CHECKBAR_PATH = os.path.join(settings.BASE_DIR, "checkbar.json")


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
    
    
def write_checkbar_file(lat, lon, fixed_name, connected_bars_12h):
    """
    Ghi dữ liệu bar/dot/line ra file JSON để debug frontend.
    File sẽ bị clear và ghi lại mỗi lần gọi API.
    """
    payload = {
        "location": fixed_name,
        "lat": lat,
        "lon": lon,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "connected_bars_12h": connected_bars_12h
    }

    try:
        with open(CHECKBAR_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("❌ Cannot write checkbar.json: %s", e)


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
# SEARCH HISTORY (CACHE & DEBUG IMPROVED)
# ---------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPremiumUser])
def add_search_history(request):
    """
    Thêm entry search history cho user. Chống duplicate (cùng user + city_name).
    Đồng thời xóa cache cũ để tránh stale data.
    """
    user = request.user
    city_name = request.data.get("city_name")
    lat = request.data.get("lat")
    lon = request.data.get("lon")

    logger.debug(f"➕ add_search_history called: user={user.username}, city_name={city_name}, lat={lat}, lon={lon}")

    if not city_name:
        logger.warning("❌ add_search_history failed: city_name missing")
        return Response({"error": "city_name is required"}, status=400)

    # Chống duplicate: nếu đã tồn tại gần đây thì update created_at
    existing = SearchHistory.objects.filter(user_id=str(user._id), city_name=city_name).first()
    if existing:
        existing.lat = lat or existing.lat
        existing.lon = lon or existing.lon
        existing.created_at = timezone.now()
        existing.save()
        logger.debug(f"♻️ Updated existing search history for user={user.username}, city_name={city_name}")

        # Xóa cache để cập nhật list mới
        cache_key = f"search_history:{str(user._id)}"
        cache.delete(cache_key)
        logger.debug(f"🗑 [CACHE DELETE] search history cache cleared for key={cache_key}")

        return Response({"message": "Updated existing search history"}, status=200)

    # Tạo mới
    sh = SearchHistory(user_id=str(user._id), city_name=city_name, lat=lat, lon=lon)
    sh.save()
    logger.debug(f"✅ Search history added for user={user.username}, city_name={city_name}")

    # Xóa cache để list mới reflect ngay
    cache_key = f"search_history:{str(user._id)}"
    cache.delete(cache_key)
    logger.debug(f"🗑 [CACHE DELETE] search history cache cleared for key={cache_key}")

    return Response({"message": "Search history added"}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPremiumUser])
def list_search_history(request):
    """
    Trả về search history dạng dropdown.
    Cache riêng theo user_id, tối đa 20 item gần đây.
    """
    user = request.user
    cache_key = f"search_history:{str(user._id)}"
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"💾 [CACHE HIT] list_search_history for user={user.username}")
        return Response(cached)

    histories = SearchHistory.objects.filter(user_id=str(user._id)).order_by('-created_at')[:20]
    dropdown = [{"id": str(h._id), "name": h.city_name, "city_name": h.city_name, "lat": h.lat, "lon": h.lon} for h in histories]

    try:
        cache.set(cache_key, dropdown, timeout=600)  # cache 10 phút
        logger.debug(f"🔁 [CACHE SET] list_search_history for user={user.username}, key={cache_key}")
    except Exception:
        logger.exception("⚠️ list_search_history: không lưu được cache")

    logger.debug(f"📄 list_search_history returned {len(dropdown)} items for user={user.username}")
    return Response(dropdown)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsPremiumUser])
def clear_search_history(request, history_id=None):
    """
    Xóa item search history theo id.
    Nếu history_id không có, xóa tất cả history của user.
    Đồng thời xóa cache để tránh stale data.
    """
    user = request.user
    logger.debug(f"🗑 clear_search_history called for user={user.username}, history_id={history_id}")

    try:
        if history_id:
            # Convert string -> ObjectId
            try:
                obj_id = ObjectId(history_id)
            except Exception:
                logger.warning(f"❌ clear_search_history failed: invalid history_id={history_id}")
                return Response({"error": "Invalid history_id"}, status=400)

            sh = SearchHistory.objects.filter(user_id=str(user._id), _id=obj_id).first()
            if sh:
                sh.delete()
                logger.debug(f"✅ Deleted search history id={history_id} for user={user.username}")
        else:
            # Xóa toàn bộ history
            deleted_count, _ = SearchHistory.objects.filter(user_id=str(user._id)).delete()
            logger.debug(f"✅ Cleared all ({deleted_count}) search history items for user={user.username}")

        # Xóa cache liên quan
        cache_key = f"search_history:{str(user._id)}"
        cache.delete(cache_key)
        logger.debug(f"🗑 [CACHE DELETE] search history cache cleared for key={cache_key}")

        return Response({"message": "Search history cleared"}, status=200)

    except Exception as e:
        logger.exception("⚠️ clear_search_history failed")
        return Response({"error": str(e)}, status=500)

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

def build_connected_bar_series(hourly, now, tz, metric, unit_hint=None, limit=12):
    """
    Build data cho mini bar dạng:
    ●──●──●──● (connected dots)

    metric:
      - feels_like
      - humidity
      - wind
      - visibility
      - uv
      - rain
    """

    points = []
    raw_values = []

    for h in hourly:
        dt_local = datetime.datetime.fromtimestamp(
            h.get("dt"), datetime.timezone.utc
        ).astimezone(tz)

        if dt_local <= now:
            continue

        if metric == "feels_like":
            value = h.get("feels_like")
        elif metric == "humidity":
            value = h.get("humidity")
        elif metric == "wind":
            value = h.get("wind_speed")
        elif metric == "visibility":
            value = h.get("visibility")
        elif metric == "uv":
            value = h.get("uvi")
        elif metric == "rain":
            value = round(h.get("pop", 0) * 100)
        else:
            value = None

        if value is None:
            continue

        raw_values.append(value)
        points.append({
            "time": dt_local.strftime("%H:%M"),
            "value": value
        })

        if len(points) >= limit:
            break

    if not raw_values:
        return None

    min_v = min(raw_values)
    max_v = max(raw_values)

    # tránh chia cho 0
    span = max(max_v - min_v, 1e-6)

    # chuẩn hoá 0–100 cho layout
    for p in points:
        p["normalized"] = round((p["value"] - min_v) / span * 100, 1)

    # xu hướng
    direction = "flat"
    if len(raw_values) >= 2:
        if raw_values[-1] > raw_values[0]:
            direction = "up"
        elif raw_values[-1] < raw_values[0]:
            direction = "down"

    return {
        "min": min_v,
        "max": max_v,
        "unit_hint": unit_hint,
        "direction": direction,
        "points": points
    }

def map_aqi_level(aqi):
    """
    Map AQI number (1–5) to human-readable text
    """
    mapping = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor",
    }
    return mapping.get(aqi, "Unknown")
def map_aqi_meta(aqi):
    """
    Return AQI metadata for UI (label, color, percent)
    """
    meta = {
        1: {"label": "Good", "color": "#4CAF50", "percent": 10},
        2: {"label": "Fair", "color": "#CDDC39", "percent": 30},
        3: {"label": "Moderate", "color": "#FFC107", "percent": 50},
        4: {"label": "Poor", "color": "#FF5722", "percent": 70},
        5: {"label": "Very Poor", "color": "#9C27B0", "percent": 90},
    }
    return meta.get(aqi)
def format_duration_hm(minutes):
    """
    Convert minutes -> '11h28p'
    """
    if minutes is None:
        return None
    h = minutes // 60
    m = minutes % 60
    return f"{h}h{m:02d}m"

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
    
    
    # 1️⃣ Kiểm tra trạng thái login tạm thời dựa trên frontend cookie
    #    Nếu cookie 'username' tồn tại → login, else → chưa login
    username_cookie = request.COOKIES.get("username")
    is_logged_in = bool(username_cookie)
    logger.debug("📄 request.COOKIES.keys(): %s", list(request.COOKIES.keys()))
    
        # --- LOG DEBUG ---
    logger.debug("🍪 username_cookie: %s", username_cookie)
    logger.debug("🔑 is_logged_in: %s", is_logged_in)
    
    # --- PREMIUM LOGIC (CHUẨN) ---
    is_premium = False
    if request.user and request.user.is_authenticated:
        is_premium = getattr(request.user, "is_premium", False)

    logger.debug("💎 is_premium: %s", is_premium)

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

        weather_cache_key = f"weather:{lat_s}:{lon_s}:{'premium' if is_premium else 'standard'}"

        # --- CACHE HIT ---
        cached_weather = cache.get(weather_cache_key)
        if cached_weather:
            logger.info(f"💾 [CACHE HIT] Trả dữ liệu từ Redis cho {weather_cache_key}")
            return Response(cached_weather)
        else:
            logger.info(f"🌍 [API CALL] Gọi OpenWeather cho {weather_cache_key}")

         # --- CALL OpenWeather 3.0 ---
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&units=metric&exclude=minutely,alerts&appid={api_key}"
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": resp.json()}, status=400)
        data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", [])
        daily = data.get("daily", [])
        
             # --- TIMEZONE OFFSET ---
        timezone_offset_seconds = data.get("timezone_offset", 0)
        tz = datetime.timezone(datetime.timedelta(seconds=timezone_offset_seconds))
        now = datetime.datetime.now(tz)
        
        # --- SUN PATH ---
        sunrise = current.get("sunrise")
        sunset = current.get("sunset")

        sun_path = None
        if sunrise and sunset:
            sunrise_local = datetime.datetime.fromtimestamp(
                sunrise, datetime.timezone.utc
            ).astimezone(tz)

            sunset_local = datetime.datetime.fromtimestamp(
                sunset, datetime.timezone.utc
            ).astimezone(tz)

            day_length_minutes = int((sunset_local - sunrise_local).total_seconds() / 60)

            sun_path = {
                "sunrise": sunrise_local.strftime("%H:%M"),
                "sunset": sunset_local.strftime("%H:%M"),
                "day_length": format_duration_hm(day_length_minutes)
            }

        # --- CURRENT WEATHER ---
        temperature = current.get("temp")
        humidity = current.get("humidity")
        condition = current.get("weather", [{}])[0].get("main", "").lower()
        icon = current.get("weather", [{}])[0].get("icon")
        wind_speed = current.get("wind_speed")
        visibility = current.get("visibility")
        rainfall = current.get("rain", {}).get("1h")
        uv_index = current.get("uvi")
        
        
        connected_bars_12h = {
        "real_feel": build_connected_bar_series(
            hourly, now, tz, "feels_like", unit_hint="temperature"
        ),
        "humidity": build_connected_bar_series(
            hourly, now, tz, "humidity", unit_hint="percent"
        ),
        "wind": build_connected_bar_series(
            hourly, now, tz, "wind", unit_hint="speed"
        ),
        "visibility": build_connected_bar_series(
            hourly, now, tz, "visibility", unit_hint="distance"
        ),
        "uv_index": build_connected_bar_series(
            hourly, now, tz, "uv", unit_hint="uv"
        ),
        "chance_of_rain": build_connected_bar_series(
            hourly, now, tz, "rain", unit_hint="percent"
        )
        
    }
        # --- DEBUG CHECK BAR DATA ---
        write_checkbar_file(
        lat=float(lat),
        lon=float(lon),
        fixed_name=fixed_name,
        connected_bars_12h=connected_bars_12h
        )


        # now = datetime.datetime.now(datetime.timezone.utc)

        # --- UPCOMING HOURS (5 hours) ---
        max_hour_count = 12 if is_premium else 5
        upcoming_hours = []
        for h in hourly:
            dt_local = datetime.datetime.fromtimestamp(h.get("dt"), datetime.timezone.utc).astimezone(tz)
            if dt_local > now and len(upcoming_hours) <  max_hour_count:
                upcoming_hours.append({
                    "time": dt_local.strftime("%Y-%m-%d %H:%M"),
                    "temp": h.get("temp"),
                    "condition": h.get("weather", [{}])[0].get("main", "").lower(),
                    "icon": h.get("weather", [{}])[0].get("icon"),
                })

        # --- CHANCE OF RAIN ---
        chance_of_rain = 0
        for h in hourly:
            dt_local = datetime.datetime.fromtimestamp(h.get("dt"), datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                chance_of_rain = round(h.get("pop", 0) * 100)
                break

        # --- DAILY FORECAST ---
        max_days = 7 if is_premium else 3
        daily_forecast_list = []
        for day_info in daily[: max_days]:
            dt_local = datetime.datetime.fromtimestamp(day_info.get("dt"), datetime.timezone.utc).astimezone(tz)
            temps = [day_info.get("temp", {}).get("max"), day_info.get("temp", {}).get("min")]
            icons = [day_info.get("weather", [{}])[0].get("icon")]
            most_common_icon = choose_daytime_icon(icons)
            daily_forecast_list.append({
                "day": dt_local.date().isoformat(),
                "temp": f"{int(max(temps))}/{int(min(temps))}",
                "icon": most_common_icon
            })
        
        # --- AIR POLLUTION (AQI) ---
        air_quality = None

        try:
            air_url = (
                f"https://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={api_key}"
            )
            air_resp = requests.get(air_url, timeout=6)

            if air_resp.status_code == 200:
                air_data = air_resp.json()
                if air_data.get("list"):
                    aqi_value = air_data["list"][0]["main"].get("aqi")
                    meta = map_aqi_meta(aqi_value)

                    if meta:
                        air_quality = {
                            "aqi": aqi_value,
                            "label": meta["label"],
                            "percent": meta["percent"],
                            "color": meta["color"],
                        }
        except Exception as e:
            logger.warning("⚠️ Cannot fetch air pollution data: %s", e)


        result = {
            "location": fixed_name,
            "temperature": temperature,
            "humidity": humidity,
            "condition": condition,
            "icon": icon,
            "wind_speed": wind_speed,
            "chance_of_rain": chance_of_rain,
            "upcoming_hours": upcoming_hours,
            "daily_forecast": daily_forecast_list,
            "visibility": visibility,
            "uv_index": uv_index,
            "rainfall": rainfall,
            "air_quality": air_quality,
            "sun_path": sun_path,
            "lat": float(lat),
            "lon": float(lon),
            "fixed_name": fixed_name,
            "connected_bars_12h": connected_bars_12h,
            "source": "OpenWeather 3.0"
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
