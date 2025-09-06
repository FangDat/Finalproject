import requests
import datetime
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer


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
            request.session['user_id'] = str(user._id)
            request.session['username'] = user.username
            request.session['is_premium'] = getattr(user, 'is_premium', False)
            return Response({
                "message": "Login successful",
                "user": user.username,
                "is_premium": request.session['is_premium']
            })
        else:
            return Response({"error": "Invalid password"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# --------------------------- LOGOUT ---------------------------
@api_view(['POST'])
def logout(request):
    request.session.flush()
    return Response({"message": "Logged out successfully"})


# --------------------------- CHECK PREMIUM ---------------------------
@api_view(['GET'])
def check_premium(request):
    is_premium = request.session.get('is_premium', False)
    return Response({"is_premium": is_premium})


# --------------------------- Helper: Get City ---------------------------
def get_city_from_coordinates(lat, lon, geocode_key):
    geocode_url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{lon}&key={geocode_key}&language=vi"
    geo_resp = requests.get(geocode_url).json()

    if geo_resp.get("results"):
        components = geo_resp["results"][0]["components"]
        # Ưu tiên city-level
        city_name = (
            components.get("city")
            or components.get("town")
            or components.get("municipality")
            or components.get("county")           # thêm county cho case Hải Châu
            or components.get("state_district")   # fallback cho vài tỉnh VN
            or components.get("state")
            or components.get("region")
            or components.get("country")
        )
        return city_name
    return None


# --------------------------- GET WEATHER ---------------------------
@api_view(['GET'])
def get_weather(request):
    api_key = "49d2545d1cdff8820a039e6e2f451ffc"  # OpenWeather key
    geocode_key = "4d1a2b6f3a1c4fb6a37b9a2efb1f6a3e"  # OpenCage key

    city = request.GET.get("city")
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    try:
        city_name = None

        # ---------------- HTML5 GEOLOCATION ----------------
        if lat and lon:
            # OpenWeather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={api_key}"

            # Lấy city-level
            city_name = get_city_from_coordinates(lat, lon, geocode_key)

        # ---------------- SEARCH BOX ----------------
        else:
            if not city:
                return Response({"error": "Cần city hoặc lat/lon"}, status=400)

            city_name = city
            current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={api_key}"

        # ---------------- CURRENT WEATHER ----------------
        current_resp = requests.get(current_url)
        current_data = current_resp.json()

        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)

        timezone_offset = current_data.get("timezone", 0)
        offset = datetime.timedelta(seconds=timezone_offset)
        tz = datetime.timezone(offset)
        now = datetime.datetime.now(tz)

        # Nếu search box thì dùng OpenWeather "name"
        if not (lat and lon):
            city_name = current_data.get("name", city_name)

        # Fix riêng cho Đà Nẵng
        if city_name and city_name.lower() in ["turan", "tourane", "da nang"]:
            city_name = "Đà Nẵng"

        # ---------------- FORECAST ----------------
        forecast_resp = requests.get(forecast_url)
        forecast_data = forecast_resp.json()

        if forecast_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu forecast", "details": forecast_data}, status=400)

        # 5 mốc giờ tới
        upcoming_hours = []
        for item in forecast_data['list']:
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                upcoming_hours.append({
                    "time": dt_local.strftime("%Y-%m-%d %H:%M"),
                    "temp": item['main']['temp'],
                    "condition": item['weather'][0]['main'].lower()
                })
            if len(upcoming_hours) >= 5:
                break

        # Chance of rain
        chance_of_rain = 0
        for item in forecast_data['list']:
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
            if dt_local > now:
                chance_of_rain = item.get("pop", 0) * 100
                break

        # Forecast 3 ngày
        daily_forecast = {}
        for item in forecast_data['list']:
            dt_utc = datetime.datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
            dt_local = dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(tz)
            day_str = dt_local.date().isoformat()

            if day_str not in daily_forecast:
                daily_forecast[day_str] = {"temps": [], "condition": item['weather'][0]['main'].lower()}

            daily_forecast[day_str]["temps"].append(item['main']['temp'])

        daily_forecast_list = []
        for day, info in list(daily_forecast.items())[:3]:
            daily_forecast_list.append({
                "day": day,
                "condition": info["condition"],
                "temp": f"{int(max(info['temps']))}/{int(min(info['temps']))}"
            })

        # ---------------- RESULT ----------------
        result = {
            "location": f"{city_name}, {current_data['sys']['country']}",
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

