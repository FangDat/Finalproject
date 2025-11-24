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
from django.core.mail import send_mail
from django.conf import settings


from ..permissions import IsPremiumUser
from ..models import User
from ..serializers import UserSerializer
from ..authentication import CustomJWTAuthentication

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
            raise AuthenticationFailed(
                "No active account found with the given credentials")

        if not check_password(password, user.password):
            raise AuthenticationFailed(
                "No active account found with the given credentials")

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
# SIGNUP → gọi hàm logic OTP
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    from .verifyotp_views import send_otp_logic, normalize_email
    username = request.data.get("username")
    raw_email = request.data.get("email")
    password = request.data.get("password")
    email = normalize_email(raw_email)
    return send_otp_logic(username, email, password)



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
            domain="localhost",
            path="/",
            samesite="Lax",
            max_age=60 * 30
        )
        resp.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=False,
            samesite="Lax",
            domain="localhost",
            path="/",
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

    # Delete cookies server-side (include domain/path used when setting)
    resp.delete_cookie("access_token", domain="localhost", path="/")
    resp.delete_cookie("refresh_token", domain="localhost", path="/")
    return resp


# ---------------------------
# REFRESH TOKEN from Cookie
# ---------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token_cookie = request.COOKIES.get("refresh_token")
    if not refresh_token_cookie:
        return Response({"error": "Refresh token missing"}, status=401)

    try:
        refresh = RefreshToken(refresh_token_cookie)
        # Tạo access token mới từ refresh
        new_access = refresh.access_token
        new_access['user_id'] = refresh.get("user_id")
        logger.debug(f"New access token generated: {str(new_access)}")
        resp = Response({"message": "Access token refreshed"})

        # Trước tiên xóa cookie access_token cũ
        resp.delete_cookie("access_token", domain="localhost", path="/")

        # Set cookie mới giống login: samesite="Lax"
        resp.set_cookie(
            key="access_token",
            value=str(new_access),
            httponly=True,
            secure=False,
            samesite="Lax",
            domain="localhost",
            path="/",
            max_age=60 * 30  # 30 phút
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
    user = request.user
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

    resp = Response({"message": "Password changed. Logged out automatically."})
    resp.delete_cookie("access_token", domain="localhost", path="/")
    resp.delete_cookie("refresh_token", domain="localhost", path="/")
    return resp



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

        resp = Response({"message": f"User '{username}' deleted successfully. Logged out automatically."})
        resp.delete_cookie("access_token", domain="localhost", path="/")
        resp.delete_cookie("refresh_token", domain="localhost", path="/")
        return resp

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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "is_premium": bool(getattr(request.user, 'is_premium', False)),
        "user_id": str(request.user.id)
    })
