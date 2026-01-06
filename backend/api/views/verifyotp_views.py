import random
import string
import logging
import json
import redis
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

# Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

OTP_EXPIRE_SECONDS = 60  
PENDING_EXPIRE_SECONDS = 300 

# ---------------------------
# HÀM PHỤ TRỢ
# ---------------------------
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


def normalize_email(raw_email):
    """Làm sạch email đầu vào triệt để"""
    if not raw_email:
        return None
    e = str(raw_email).strip()

    # Xoá tất cả dấu ngoặc kép và nháy đơn bao quanh hoặc lẫn trong email
    e = e.replace('"', '').replace("'", '')

    # Nếu email vẫn còn ký tự không hợp lệ thì loại bỏ thêm khoảng trắng
    e = e.strip()

    # Tránh trường hợp bị thêm dấu ngoặc khi stringify
    if e.startswith('"') and e.endswith('"'):
        e = e[1:-1].strip()
    if e.startswith("'") and e.endswith("'"):
        e = e[1:-1].strip()
    logger.debug(f"normalize_email() input={repr(raw_email)} → output={repr(e)}")
    return e or None


    


# ---------------------------
# LOGIC GỬI OTP DÙNG CHUNG (CHO SIGNUP & API send_otp)
# ---------------------------
def send_otp_logic(username, email, password):
    """
    Hàm logic nội bộ để gửi OTP (dùng lại trong signup).
    Không sử dụng request.
    """
    from ..models import User

    logger.debug(f"📨 send_otp_logic() username={username}, email={email}")

    if not all([username, email, password]):
        return Response({"error": "Missing required fields"}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({"email": ["This email is already in use!"]}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"username": ["Username already exists!"]}, status=400)


    # Sinh mã OTP và lưu Redis
    otp = generate_otp()
    otp_key = f"otp:{email}"
    pending_key = f"pending_user:{email}"
    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)
    email = normalize_email(email)
    redis_client.setex(pending_key, PENDING_EXPIRE_SECONDS, json.dumps({
        "username": username,
        "email": email,
        "password": password
    }))


    logger.debug(f"💾 Redis saved OTP={otp} & pending user for {email}")

    # Gửi mail
    subject = "VietCloud Email Verification Code"
    message = f"Hello {username},\n\nYour VietCloud verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\n— VietCloud Team"
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception:
        logger.exception("❌ Failed to send OTP mail")
        redis_client.delete(otp_key)
        redis_client.delete(pending_key)
        return Response({"error": "Failed to send OTP email"}, status=500)

    return Response({"message": "OTP sent successfully"}, status=200)


# ---------------------------
# API send_otp
# ---------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    username = request.data.get("username")
    raw_email = request.data.get("email")
    password = request.data.get("password")
    email = normalize_email(raw_email)

    return send_otp_logic(username, email, password)


# ---------------------------
# VERIFY OTP
# ---------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    raw_email = request.data.get("email")
    otp_input = request.data.get("otp")
    email = normalize_email(raw_email)

    if not all([email, otp_input]):
        return Response({"error": "Missing email or OTP"}, status=400)

    otp_key = f"otp:{email}"
    pending_key = f"pending_user:{email}"

    stored_otp = redis_client.get(otp_key)
    if not stored_otp:
        return Response({"error": "OTP expired or not found"}, status=400)
    if str(otp_input).strip() != str(stored_otp).strip():
        return Response({"error": "Invalid OTP"}, status=400)

    pending_data_raw = redis_client.get(pending_key)
    if not pending_data_raw:
        return Response({"error": "Pending user data expired"}, status=400)

    try:
        pending_data = json.loads(pending_data_raw)
        email_clean = normalize_email(pending_data.get("email"))
        pending_data["email"] = email_clean

    except Exception:
        return Response({"error": "Internal server error"}, status=500)

    from ..serializers import UserSerializer
    pending_data["email"] = normalize_email(pending_data.get("email"))
    serializer = UserSerializer(data=pending_data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    user = serializer.save()

    # Xoá Redis
    redis_client.delete(otp_key)
    redis_client.delete(pending_key)

    # JWT Tokens
    refresh = RefreshToken.for_user(user)
    refresh['user_id'] = str(user._id)
    access = refresh.access_token
    access['user_id'] = str(user._id)

    resp = Response({
        "message": "Email verified and user registered successfully",
        "username": getattr(user, "username", ""),
        "email": getattr(user, "email", ""),
        "user_id": str(getattr(user, "_id", "")),
    }, status=201)

    # Set HttpOnly cookies
    resp.set_cookie("access_token", str(access), httponly=True, secure=False, domain="localhost", path="/", samesite="Lax", max_age=60*30)
    resp.set_cookie("refresh_token", str(refresh), httponly=True, secure=False, domain="localhost", path="/", samesite="Lax", max_age=60*60*24*7)
    # Cookies frontend
    
    resp.set_cookie("username", str(user.username), httponly=False, domain="localhost", path="/", samesite="Lax", max_age=60*60*24*7)
    
    clean_email = normalize_email(user.email)
    if clean_email and clean_email.startswith('"') and clean_email.endswith('"'):
        try:
            clean_email = json.loads(clean_email)
        except Exception:
            clean_email = clean_email.strip('"').strip("'")

    resp.set_cookie(
    "email",
    clean_email,
    httponly=False,
    domain="localhost",
    path="/",
    samesite="Lax",
    max_age=60*60*24*7
    )


    return resp


# ---------------------------
# RESEND OTP
# ---------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    raw_email = request.data.get("email")
    email = normalize_email(raw_email)

    if not email:
        return Response({"error": "Email is required"}, status=400)

    pending_key = f"pending_user:{email}"
    otp_key = f"otp:{email}"

    if not redis_client.get(pending_key):
        return Response({"error": "No pending signup found"}, status=400)

    ttl = redis_client.ttl(otp_key)
    if ttl and ttl > 0:
        return Response({
            "error": "OTP still valid. Please wait before requesting again.",
            "seconds_remaining": ttl
        }, status=429)

    otp = generate_otp()
    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)
    logger.debug(f"💾 Redis resend saved OTP={otp} & pending user for {email}")

    subject = "VietCloud Email Verification Code (Resent)"
    message = f"Hello,\n\nYour new VietCloud OTP code is: {otp}\n\nExpires in 10 minutes.\n\n— VietCloud Team"
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception:
        return Response({"error": "Failed to resend OTP"}, status=500)

    return Response({"message": "New OTP sent successfully"}, status=200)

# ============================
# CHANGE EMAIL - SEND OTP LOGIC (FIXED)
# ============================
def send_change_email_otp_logic(user, raw_new_email):
    from ..models import User

    new_email = normalize_email(raw_new_email)
    logger.debug(
        f"📨 [CHANGE_EMAIL][SEND_OTP] user={user.username}, new_email={new_email}"
    )

    if not new_email:
        return Response({"error": "Email is required"}, status=400)

    if User.objects.filter(email=new_email).exists():
        return Response({"error": "Email already in use"}, status=400)

    otp_key = f"change_email_otp:{user.id}"
    pending_key = f"change_email_pending:{user.id}"

    # 🔥 xoá OTP cũ nếu tồn tại
    redis_client.delete(otp_key)

    otp = generate_otp()

    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)
    redis_client.setex(
        pending_key,
        PENDING_EXPIRE_SECONDS,
        json.dumps({
            "user_id": str(user.id),
            "new_email": new_email
        })
    )

    # 🐞 debug OTP
    logger.debug(
        f"💾 [CHANGE_EMAIL] Redis saved OTP={otp} for user_id={user.id}"
    )

    subject = "VietCloud – Confirm your new email"
    message = (
        f"Hello {user.username},\n\n"
        f"Your OTP to change email is: {otp}\n\n"
        f"This code will expire in 10 minutes.\n\n"
        "— VietCloud Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email])
    except Exception:
        logger.exception("❌ Failed to send change email OTP")
        redis_client.delete(otp_key)
        redis_client.delete(pending_key)
        return Response({"error": "Failed to send OTP"}, status=500)

    return Response({"message": "OTP sent to new email"}, status=200)

# ============================
# CHANGE EMAIL - VERIFY OTP (FIXED)
# ============================
def verify_change_email_otp_logic(user, otp_input):
    otp_key = f"change_email_otp:{user.id}"
    pending_key = f"change_email_pending:{user.id}"

    stored_otp = redis_client.get(otp_key)
    if not stored_otp:
        return Response({"error": "OTP expired or not found"}, status=400)

    logger.debug(
        f"🔍 [CHANGE_EMAIL][VERIFY] input={otp_input}, stored={stored_otp}"
    )

    if str(otp_input).strip() != str(stored_otp).strip():
        return Response({"error": "Invalid OTP"}, status=400)

    pending_raw = redis_client.get(pending_key)
    if not pending_raw:
        return Response({"error": "Pending email change expired"}, status=400)

    try:
        pending_data = json.loads(pending_raw)
        new_email = normalize_email(pending_data.get("new_email"))
    except Exception:
        logger.exception("❌ Pending parse error")
        return Response({"error": "Internal server error"}, status=500)

    user.email = new_email
    user.save()

    redis_client.delete(otp_key)
    redis_client.delete(pending_key)

    logger.debug(
        f"✅ [CHANGE_EMAIL] Email updated to {new_email} for user={user.username}"
    )

    resp = Response({
        "message": "Email changed successfully. Logged out automatically.",
        "new_email": new_email
    }, status=200)

    resp.delete_cookie("access_token", domain="localhost", path="/")
    resp.delete_cookie("refresh_token", domain="localhost", path="/")
    
    return resp 

# ============================
# CHANGE EMAIL - RESEND OTP (FIXED)
# ============================
def resend_change_email_otp_logic(user):
    otp_key = f"change_email_otp:{user.id}"
    pending_key = f"change_email_pending:{user.id}"

    pending_raw = redis_client.get(pending_key)
    if not pending_raw:
        return Response({"error": "Pending email change expired"}, status=400)

    ttl = redis_client.ttl(otp_key)
    if ttl and ttl > 0:
        return Response({
            "error": "OTP still valid. Please wait before requesting again.",
            "seconds_remaining": ttl
        }, status=429)

    # 🔥 XOÁ OTP CŨ
    redis_client.delete(otp_key)

    pending_data = json.loads(pending_raw)
    new_email = normalize_email(pending_data.get("new_email"))

    otp = generate_otp()

    # ✅ SET LẠI OTP
    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)

    # ✅ RESET TTL CỦA PENDING (CỰC KỲ QUAN TRỌNG)
    redis_client.expire(pending_key, PENDING_EXPIRE_SECONDS)

    logger.debug(
        f"🔁 [CHANGE_EMAIL][RESEND] new OTP={otp}, pending TTL reset for user_id={user.id}"
    )

    subject = "VietCloud – Your new email OTP (Resent)"
    message = (
        f"Hello {user.username},\n\n"
        f"Your new OTP code is: {otp}\n\n"
        "— VietCloud Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_email])
    except Exception:
        logger.exception("❌ Failed to resend change email OTP")
        return Response({"error": "Failed to resend OTP"}, status=500)

    return Response({"message": "OTP resent successfully"}, status=200)

# ============================
# FORGOT PASSWORD - SEND OTP
# ============================
def send_forgot_password_otp_logic(raw_email):
    from ..models import User

    email = normalize_email(raw_email)
    logger.debug(f"📨 [FORGOT_PWD][SEND] email={email}")

    if not email:
        return Response({"error": "Email is required"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # ❗ Không leak email tồn tại hay không
        return Response({"message": "If the email exists, OTP has been sent"}, status=200)

    otp_key = f"forgot_pwd_otp:{email}"
    pending_key = f"forgot_pwd_pending:{email}"

    # Xoá OTP cũ
    redis_client.delete(otp_key)

    otp = generate_otp()
    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)
    redis_client.setex(
        pending_key,
        PENDING_EXPIRE_SECONDS,
        json.dumps({"email": email})
    )

    logger.debug(f"💾 [FORGOT_PWD] OTP={otp} saved for {email}")

    subject = "VietCloud – Reset your password"
    message = (
        f"Hello {user.username},\n\n"
        f"Your OTP to reset password is: {otp}\n\n"
        "This code will expire in 10 minutes.\n\n"
        "— VietCloud Team"
    )

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception:
        logger.exception("❌ Failed to send forgot password OTP")
        redis_client.delete(otp_key)
        redis_client.delete(pending_key)
        return Response({"error": "Failed to send OTP"}, status=500)

    return Response({"message": "OTP sent successfully"}, status=200)


# ============================
# FORGOT PASSWORD - VERIFY OTP
# ============================
def verify_forgot_password_otp_logic(raw_email, otp_input):
    email = normalize_email(raw_email)

    if not email or not otp_input:
        return Response({"error": "Email and OTP required"}, status=400)

    otp_key = f"forgot_pwd_otp:{email}"
    pending_key = f"forgot_pwd_pending:{email}"

    stored_otp = redis_client.get(otp_key)
    if not stored_otp:
        return Response({"error": "OTP expired or not found"}, status=400)

    if str(otp_input).strip() != str(stored_otp).strip():
        return Response({"error": "Invalid OTP"}, status=400)

    if not redis_client.get(pending_key):
        return Response({"error": "Reset session expired"}, status=400)

    logger.debug(f"✅ [FORGOT_PWD] OTP verified for {email}")

    return Response({"message": "OTP verified"}, status=200)


# ============================
# FORGOT PASSWORD - RESET
# ============================
def reset_password_logic(raw_email, new_password, confirm_password):
    from ..models import User

    email = normalize_email(raw_email)
    pending_key = f"forgot_pwd_pending:{email}"
    otp_key = f"forgot_pwd_otp:{email}"

    if not redis_client.get(pending_key):
        return Response({"error": "Reset session expired"}, status=400)

    if not new_password or not confirm_password:
        return Response({"error": "Password required"}, status=400)

    if len(new_password) < 8:
        return Response({"error": "Password must be at least 8 characters"}, status=400)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    user.password = new_password
    user.save()

    # Cleanup Redis
    redis_client.delete(otp_key)
    redis_client.delete(pending_key)

    logger.debug(f"🔐 [FORGOT_PWD] Password reset success for {email}")

    return Response(
        {"message": "Password reset successfully. Please login again."},
        status=200
    )


# ============================
# FORGOT PASSWORD - RESEND OTP
# ============================
def resend_forgot_password_otp_logic(raw_email):
    email = normalize_email(raw_email)
    otp_key = f"forgot_pwd_otp:{email}"
    pending_key = f"forgot_pwd_pending:{email}"

    if not redis_client.get(pending_key):
        return Response({"error": "Reset session expired"}, status=400)

    ttl = redis_client.ttl(otp_key)
    if ttl and ttl > 0:
        return Response(
            {"error": "OTP still valid", "seconds_remaining": ttl},
            status=429
        )

    redis_client.delete(otp_key)
    otp = generate_otp()
    redis_client.setex(otp_key, OTP_EXPIRE_SECONDS, otp)

    subject = "VietCloud – Reset password OTP (Resent)"
    message = f"Your new OTP is: {otp}"

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    except Exception:
        return Response({"error": "Failed to resend OTP"}, status=500)

    return Response({"message": "OTP resent successfully"}, status=200)
