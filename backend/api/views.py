import requests
import datetime
from urllib.parse import quote
import logging
import re

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import check_password

from .permissions import IsPremiumUser
from .models import User
from .serializers import UserSerializer
from .authentication import CustomJWTAuthentication

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------
# Custom Token Serializer
# ---------------------------
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user._id)
        return token

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise AuthenticationFailed("Username and password required")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AuthenticationFailed("No active account found with the given credentials")

        if not check_password(password, user.password):
            raise AuthenticationFailed("No active account found with the given credentials")

        refresh = self.get_token(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "username": user.username,
            "is_premium": bool(getattr(user, "is_premium", False)),
            "user_id": str(user._id),
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
# LOGIN → set HttpOnly cookies
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
        if not check_password(password, user.password):
            return Response({"error": "Invalid password"}, status=400)

        refresh = RefreshToken.for_user(user)
        refresh['user_id'] = str(user._id)
        access = refresh.access_token
        access['user_id'] = str(user._id)

        resp = Response({
            "message": "Login successful",
            "username": user.username,
            "email": getattr(user, "email", ""),
            "is_premium": bool(getattr(user, 'is_premium', False)),
            "user_id": str(user._id)
        })

        # Set cookies HttpOnly
        resp.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=60 * 30
        )
        resp.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=60 * 60 * 24 * 7
        )
        return resp

    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)


# ---------------------------
# LOGOUT → clear cookies
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    resp = Response({"message": "Logged out successfully"})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    return resp


# ---------------------------
# REFRESH TOKEN from Cookie
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"error": "Refresh token missing"}, status=401)

    try:
        refresh = RefreshToken(refresh_token)
        access = refresh.access_token
        access['user_id'] = refresh.get("user_id")

        resp = Response({"message": "Access token refreshed"})
        resp.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=60 * 30
        )
        return resp
    except TokenError:
        return Response({"error": "Invalid or expired refresh token"}, status=401)


# ---------------------------
# CHANGE PASSWORD
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user  # ✅ lấy từ CustomJWTAuthentication
    current_password = request.data.get("current_password", "")
    new_password = request.data.get("new_password", "")
    confirm_password = request.data.get("confirm_password", "")

    if not check_password(current_password, user.password):
        return Response({"error": "Current password is incorrect"}, status=400)
    if check_password(new_password, user.password):
        return Response({"error": "New password cannot be the same"}, status=400)
    if len(new_password) < 8:
        return Response({"error": "Password must be at least 8 characters"}, status=400)
    if not re.search(r"[a-z]", new_password):
        return Response({"error": "Must contain lowercase"}, status=400)
    if not re.search(r"[A-Z]", new_password):
        return Response({"error": "Must contain uppercase"}, status=400)
    if not re.search(r"\d", new_password):
        return Response({"error": "Must contain number"}, status=400)
    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    user.password = new_password
    user.save()
    return Response({"message": "Password changed. Please login again."})


# ---------------------------
# DELETE ACCOUNT
# ---------------------------
@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    try:
        user = request.user
        username_input = request.data.get("username")
        password_input = request.data.get("password")
        confirm_password_input = request.data.get("confirm_password")

        if not username_input or not password_input or not confirm_password_input:
            return Response({"error": "username, password and confirm_password are required"}, status=400)

        if username_input != getattr(user, "username", None):
            return Response({"error": "Username does not match authenticated user"}, status=403)

        if password_input != confirm_password_input:
            return Response({"error": "Password and confirmation do not match"}, status=400)

        if not check_password(password_input, user.password):
            return Response({"error": "Password is incorrect"}, status=403)

        db_user = User.objects.get(username=user.username)
        username = db_user.username
        db_user.delete()

        logger.info(f"User '{username}' deleted by user request.")
        return Response({"message": f"User '{username}' deleted successfully"}, status=200)
    except Exception as e:
        logger.exception("delete_account failed")
        return Response({"error": "Failed to delete account", "details": str(e)}, status=500)


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

