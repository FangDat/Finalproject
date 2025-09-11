import requests
import datetime
from urllib.parse import quote
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# --------------------------- SIGNUP ---------------------------
@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"}, status=201)
    return Response(serializer.errors, status=400)


# --------------------------- LOGIN ---------------------------
@api_view(['POST'])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    try:
        user = User.objects.get(username=username)
        if check_password(password, user.password):
            return Response({
                "message": "Login successful",
                "user": user.username,
                "is_premium": getattr(user, 'is_premium', False)
            })
        else:
            return Response({"error": "Invalid password"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# --------------------------- Helpers ---------------------------
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
    district = comps.get("suburb") or comps.get("city_district") or comps.get("county")
    city = comps.get("city") or comps.get("town")
    state = comps.get("state") or comps.get("province")

    if district and city:
        return f"{clean_city_name(district)}, {clean_city_name(city)}"
    if district and state:
        return f"{clean_city_name(district)}, {clean_city_name(state)}"
    if city and state:
        return f"{clean_city_name(city)}, {clean_city_name(state)}"
    return clean_city_name(fallback)


# --------------------------- Autocomplete ---------------------------
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
        main_keys = ["city", "town", "village", "municipality", "county", "state", "province", "region"]
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

        if display.lower() == q.lower():
            exact_matches.append({
                "name": display,
                "lat": geometry.get("lat"),
                "lon": geometry.get("lng"),
                "is_vn": (comps.get("country_code", "").lower() == "vn"),
                "raw": r.get("formatted", "")
            })
        else:
            rank = get_place_rank(comps)
            scored.append((
                rank,
                score_result(r),
                {
                    "name": display,
                    "lat": geometry.get("lat"),
                    "lon": geometry.get("lng"),
                    "is_vn": (comps.get("country_code", "").lower() == "vn"),
                    "raw": r.get("formatted", "")
                }
            ))

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
        key = item["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(item)

    return Response(suggestions)


# --------------------------- Helper: Get City from Coordinates ---------------------------
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


# --------------------------- GET WEATHER ---------------------------
@api_view(['GET'])
def get_weather(request):
    api_key = "49d2545d1cdff8820a039e6e2f451ffc"
    geocode_key = "c173e9b1e4c14ee3845dfa894f82a9c7"

    city_input = request.GET.get("city")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    name = request.GET.get("name")  # Tên hiển thị frontend gửi lên

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

            logger.debug(f"City chosen: {city_name}, lat={lat}, lon={lon}")
            print(f"[DEBUG] City chosen: {city_name}, lat={lat}, lon={lon}")

        if not lat or not lon:
            return Response({"error": "Không lấy được tọa độ cho địa điểm"}, status=400)

        # Call OpenWeather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"

        current_resp = requests.get(current_url)
        current_data = current_resp.json()
        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)

        timezone_offset = current_data.get("timezone", 0)
        offset = datetime.timedelta(seconds=timezone_offset)
        tz = datetime.timezone(offset)
        now = datetime.datetime.now(tz)

        forecast_resp = requests.get(forecast_url)
        forecast_data = forecast_resp.json()
        if forecast_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu forecast", "details": forecast_data}, status=400)

        # Forecast processing
        upcoming_hours, daily_forecast = [], {}
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)

            if dt_local > now and len(upcoming_hours) < 5:
                upcoming_hours.append({
                    "time": dt_local.strftime("%Y-%m-%d %H:%M"),
                    "temp": item['main']['temp'],
                    "condition": item['weather'][0]['main'].lower()
                })

            day_str = dt_local.date().isoformat()
            if day_str not in daily_forecast:
                daily_forecast[day_str] = {"temps": [], "condition": item['weather'][0]['main'].lower()}
            daily_forecast[day_str]["temps"].append(item['main']['temp'])

        chance_of_rain = 0
        for item in forecast_data.get('list', []):
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                chance_of_rain = item.get("pop", 0) * 100
                break

        daily_forecast_list = []
        for day, info in list(daily_forecast.items())[:3]:
            daily_forecast_list.append({
                "day": day,
                "condition": info["condition"],
                "temp": f"{int(max(info['temps']))}/{int(min(info['temps']))}"
            })

        result = {
            "location": city_name,
            "temperature": current_data['main']['temp'],
            "humidity": current_data['main']['humidity'],
            "condition": current_data['weather'][0]['main'].lower(),
            "wind_speed": current_data['wind']['speed'],
            "chance_of_rain": round(chance_of_rain),
            "upcoming_hours": upcoming_hours,
            "daily_forecast": daily_forecast_list,
            "source": "OpenWeather"
        }

        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)




# from django.shortcuts import render
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from django.contrib.auth.hashers import check_password
# from .models import User
# from .serializers import UserSerializer


# @api_view(['POST'])
# def signup(request):
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({"message": "User created successfully!"}, status=201)
#     return Response(serializer.errors, status=400)


# @api_view(['POST'])
# def login(request):
#     username = request.data.get("username")
#     password = request.data.get("password")
#     try:
#         user = User.objects.get(username=username)
#         if check_password(password, user.password):
#             return Response({"message": "Login successful", "user": user.username})
#         else:
#             return Response({"error": "Invalid password"}, status=400)
#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=404)


# # Create your views here.
# @api_view(['POST'])
# def signup(request):
#     print("DEBUG request.data:", request.data)  # 👈 in ra dữ liệu nhận được
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         return Response({"message": "User created successfully"}, status=201)
#     else:
#         print("DEBUG serializer.errors:", serializer.errors)  # 👈 in lỗi chi tiết
#         return Response(serializer.errors, status=400)
# code cu~ nhat

# from django.shortcuts import render
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from django.contrib.auth.hashers import check_password, make_password
# from .models import User
# from .serializers import UserSerializer
# from django.contrib.auth import authenticate, login as dj_login, logout as dj_logout
# from django.contrib.auth.hashers import check_password
# from django.contrib.auth import login as dj_login
# import requests
# import datetime

# # ---------------------------
# # SIGNUP
# # ---------------------------
# @api_view(['POST'])
# def signup(request):
#     print("DEBUG request.data:", request.data)   # 👈 in ra dữ liệu nhận được
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         return Response({"message": "User created successfully"}, status=201)
#     else:
#         print("DEBUG serializer.errors:", serializer.errors)  # 👈 in lỗi chi tiết
#         return Response(serializer.errors, status=400)


# # ---------------------------
# # LOGIN
# # ---------------------------
# @api_view(['POST'])
# def login(request):
#     username = request.data.get("username")
#     password = request.data.get("password")

#     if not username or not password:
#         return Response({"error": "Username and password are required"}, status=400)

#     try:
#         user = User.objects.get(username=username)
#         if check_password(password, user.password):
#             # ---------------------------
#             # SESSION-BASED LOGIN
#             # ---------------------------
#             request.session['user_id'] = str(user._id)
#             request.session['username'] = user.username
#             request.session['is_premium'] = getattr(user, 'is_premium', False)

#             return Response({
#                 "message": "Login successful",
#                 "user": user.username,
#                 "is_premium": request.session['is_premium']
#             })
#         else:
#             return Response({"error": "Invalid password"}, status=400)
#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=404)


# # ---------------------------
# # LOGOUT
# # ---------------------------
# @api_view(['POST'])
# def logout(request):
#     """
#     Logout user và xóa toàn bộ session.
#     """
#     request.session.flush()
#     return Response({"message": "Logged out successfully"})


# # ---------------------------
# # CHECK PREMIUM
# # ---------------------------
# @api_view(['GET'])
# def check_premium(request):
#     """
#     Kiểm tra user hiện tại có quyền premium hay không.
#     Trả về: {"is_premium": True/False}
#     """
#     is_premium = request.session.get('is_premium', False)
#     return Response({"is_premium": is_premium})


# @api_view(['GET'])
# def get_weather(request):
#     city = "Ha Noi"
#     api_key = "49d2545d1cdff8820a039e6e2f451ffc"  # thay bằng key của bạn

#     try:
#         # --- Current weather ---
#         url_current = f"http://pro.openweathermap.org/data/2.5/weather?q={city},VN&units=metric&appid={api_key}"
#         resp_current = requests.get(url_current)
#         if resp_current.status_code != 200:
#             return Response({"error": "Không lấy được dữ liệu thời tiết hiện tại", "details": resp_current.json()}, status=400)
#         data_current = resp_current.json()

#         result = {
#             "location": f"{data_current['name']}, {data_current['sys']['country']}",
#             "temperature": data_current['main']['temp'],
#             "humidity": data_current['main']['humidity'],
#             "condition": data_current['weather'][0]['description'],
#             "wind_speed": data_current['wind']['speed'],
#             "hourly_forecast": [],
#             "daily_forecast": [],
#             "source": "OpenWeather"
#         }

#         # --- 5 khung giờ cố định: 6,9,12,15,18 ---
#         url_forecast = f"http://pro.openweathermap.org/data/2.5/forecast?q={city},VN&units=metric&appid={api_key}"
#         resp_forecast = requests.get(url_forecast)
#         if resp_forecast.status_code != 200:
#             return Response({"error": "Không lấy được dữ liệu forecast", "details": resp_forecast.json()}, status=400)
#         data_forecast = resp_forecast.json()

#         hours_needed = [6, 9, 12, 15, 18]
#         today = datetime.datetime.now().date()

#         # Lọc forecast theo giờ cố định
#         for item in data_forecast['list']:
#             dt = datetime.datetime.fromtimestamp(item['dt'])
#             if dt.date() == today and dt.hour in hours_needed:
#                 result['hourly_forecast'].append({
#                     "time": dt.strftime("%H:%M"),
#                     "temp": item['main']['temp'],
#                     "condition": item['weather'][0]['description']
#                 })

#         # Lấy dự báo 3 ngày tới (dựa vào forecast ngày hôm nay trở đi)
#         daily_temp = {}
#         for item in data_forecast['list']:
#             dt = datetime.datetime.fromtimestamp(item['dt'])
#             day_str = dt.strftime("%Y-%m-%d")
#             if day_str not in daily_temp:
#                 daily_temp[day_str] = {"max": item['main']['temp_max'], "min": item['main']['temp_min'], "icon": item['weather'][0]['description']}
#             else:
#                 daily_temp[day_str]['max'] = max(daily_temp[day_str]['max'], item['main']['temp_max'])
#                 daily_temp[day_str]['min'] = min(daily_temp[day_str]['min'], item['main']['temp_min'])

#         # Chỉ lấy 3 ngày đầu
#         for i, (day, val) in enumerate(daily_temp.items()):
#             if i >= 3:
#                 break
#             dt_obj = datetime.datetime.strptime(day, "%Y-%m-%d")
#             result['daily_forecast'].append({
#                 "day": dt_obj.strftime("%a"),
#                 "icon": val['icon'],
#                 "temp": f"{int(val['max'])}/{int(val['min'])}"
#             })

#         return Response(result)

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)

# code chua fix

