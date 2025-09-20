# backend/api/views.py
import requests
import datetime
from urllib.parse import quote
import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPremiumUser

from .models import User, RevokedToken
from .serializers import UserSerializer
from .authentication import CustomJWTAuthentication
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------
# Custom TokenObtainPairSerializer
# ---------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Override validate để dùng custom User model (MongoDB) thay vì authenticate().
    Chèn 'user_id' (_id) vào payload để CustomJWTAuthentication hoạt động.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Thêm user_id vào token payload
        token['user_id'] = str(user._id)  # MongoDB _id -> str
        return token

    def validate(self, attrs):
        username = attrs.get(self.username_field) or attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise AuthenticationFailed("Username and password required")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed("No active account found with the given credentials")

        if not check_password(password, user.password):
            raise AuthenticationFailed("No active account found with the given credentials")

        # Dùng get_token để tạo JWT, payload đã có user_id
        refresh = self.get_token(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "username": user.username,
            "is_premium": bool(getattr(user, "is_premium", False)),
            "user_id": str(user._id),  # MongoDB _id
        }
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# ---------------------------
# SIGNUP
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"}, status=201)
    return Response(serializer.errors, status=400)


# ---------------------------
# LOGIN
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)

    try:
        user = User.objects.get(username=username)
        if check_password(password, user.password):
            refresh = RefreshToken.for_user(user)
            # Thêm user_id vào payload của refresh token và access token
            refresh['user_id'] = str(user._id)
            access = refresh.access_token
            access['user_id'] = str(user._id)

            return Response({
                "message": "Login successful",
                "user": user.username,
                "email": getattr(user, "email", ""),
                "is_premium": bool(getattr(user, 'is_premium', False)),
                "refresh": str(refresh),
                "access": str(access),
                "user_id": str(user._id)
            })
        else:
            return Response({"error": "Invalid password"}, status=400)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)



# ---------------------------
# LOGOUT (revoke refresh token)
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    token_str = request.data.get("refresh")
    if not token_str:
        return Response({"error": "refresh token required"}, status=400)

    try:
        rt = RefreshToken(token_str)
        jti = rt.get("jti")
        exp = rt.get("exp")
        user_id = rt.get("user_id") or None

        expires_at = None
        if exp:
            try:
                expires_at = datetime.datetime.fromtimestamp(int(exp), tz=timezone.utc)
            except Exception:
                expires_at = None

        if jti:
            if not RevokedToken.objects.filter(jti=jti).exists():
                RevokedToken.objects.create(
                    jti=jti,
                    token=token_str,
                    user_id=str(user_id) if user_id else None,
                    expires_at=expires_at
                )
            return Response({"message": "Token revoked"}, status=200)
        else:
            return Response({"error": "Token has no jti"}, status=400)
    except Exception as e:
        logger.exception("logout failed")
        return Response({"error": "Invalid token", "details": str(e)}, status=400)


# ---------------------------
# CHANGE PASSWORD
# ---------------------------
import re
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")
    confirm_password = request.data.get("confirm_password", "")

    # Kiểm tra mật khẩu hiện tại
    if not check_password(current_password, user.password):
        return Response({"error": "Current password is incorrect"}, status=400)
    
    if check_password(new_password, user.password):
        return Response({"error": "New password cannot be the same as the old password"}, status=400)

    # Validate mật khẩu mới
    if len(new_password) < 8:
        return Response({"error": "Password must be at least 8 characters"}, status=400)
    if not re.search(r"[a-z]", new_password):
        return Response({"error": "Password must contain at least one lowercase letter"}, status=400)
    if not re.search(r"[A-Z]", new_password):
        return Response({"error": "Password must contain at least one uppercase letter"}, status=400)
    if not re.search(r"\d", new_password):
        return Response({"error": "Password must contain at least one number"}, status=400)
    if new_password != confirm_password:
        return Response({"error": "New password and confirmation do not match"}, status=400)

    # Cập nhật mật khẩu
    user.password = new_password
    user.save()

    return Response({"message": "Password changed successfully, System automatically logged out, please log in again..."})

# ---------------------------
# CHECK PREMIUM
# ---------------------------
# @api_view(['GET'])
# @permission_classes([AllowAny])  # Cho phép test token mà không cần login DRF chuẩn
# def check_premium(request):
#     """
#     Test API check premium: lấy token từ header Authorization và xác thực
#     """
#     auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION")
#     if not auth_header:
#         return Response({"error": "Authorization header missing"}, status=401)

#     try:
#         # Token dạng "Bearer <token>"
#         prefix, token_str = auth_header.split()
#         if prefix.lower() != "bearer":
#             return Response({"error": "Authorization header must start with Bearer"}, status=401)
#     except ValueError:
#         return Response({"error": "Invalid Authorization header"}, status=401)

#     try:
#         validated_token = CustomJWTAuthentication().get_validated_token(token_str)
#         user = CustomJWTAuthentication().get_user(validated_token)
#     except AuthenticationFailed as e:
#         return Response({"error": "Token invalid or expired", "details": str(e)}, status=401)
#     except Exception as e:
#         return Response({"error": "Token verification failed", "details": str(e)}, status=400)

#     return Response({
#         "user_id": str(user._id),
#         "username": user.username,
#         "is_premium": bool(getattr(user, "is_premium", False)),
#         "token_received": token_str
#     })

# ---------------------------
# CHECK PREMIUM
# ---------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsPremiumUser])
def check_premium(request):
    user = request.user
    return Response({
        "username": user.username,
        "is_premium": bool(getattr(user, 'is_premium', False))
    })


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
# GET WEATHER
# ---------------------------
@api_view(['GET'])
def get_weather(request):
    api_key = "49d2545d1cdff8820a039e6e2f451ffc"
    geocode_key = "c173e9b1e4c14ee3845dfa894f82a9c7"

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
        if current_resp.status_code != 200:
            return Response({"error": "Không lấy được dữ liệu thời tiết", "details": current_data}, status=400)

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
        logger.exception("get_weather failed")
        return Response({"error": str(e)}, status=500)

