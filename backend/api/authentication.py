
# backend/api/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Override JWTAuthentication để:
    1️⃣ Hỗ trợ lấy token từ cookie 'access_token' nếu không có header.
    2️⃣ get_user xử lý MongoDB ObjectId.
    """

    def authenticate(self, request):
        """
        Trả về (user, validated_token) hoặc None.
        """
        # -----------------
        # 1️⃣ Thử lấy token từ header Authorization
        # -----------------
        header_auth = self.get_header(request)
        logger.debug(f"Header Authorization: {header_auth}")

        if header_auth is not None:
            raw_token = self.get_raw_token(header_auth)
            if raw_token is not None:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    user = self.get_user(validated_token)
                    logger.debug(
                        f"Authenticated user from header: {user.username}")
                    return (user, validated_token)
                except Exception as e:
                    logger.debug(f"Header token invalid: {e}")
                    # Không raise, fallback sang cookie

        # -----------------
        # 2️⃣ Thử lấy token từ cookie 'access_token'
        # -----------------
        cookie_token = request.COOKIES.get("access_token")
        logger.debug(f"Cookie access_token: {cookie_token}")

        if cookie_token is not None:
            try:
                validated_token = self.get_validated_token(cookie_token)
                user = self.get_user(validated_token)
                logger.debug(
                    f"Authenticated user from cookie: {user.username}")
                return (user, validated_token)
            except Exception as e:
                logger.debug(f"Cookie token invalid: {e}")
                return None

        # -----------------
        # 3️⃣ Không tìm thấy token
        # -----------------
        logger.debug("No JWT token found in header or cookie")
        return None

    def get_user(self, validated_token):
        """
        Lấy user từ validated_token MongoDB ObjectId
        """
        user_id = validated_token.get("user_id")
        if not user_id:
            logger.debug("Token không có user_id")
            raise AuthenticationFailed(
                "Token contained no user_id", code="no_user_id")

        logger.debug(f"Token user_id: {user_id}")

        # Convert string user_id → ObjectId
        try:
            oid = ObjectId(user_id)
        except Exception as e:
            logger.debug(f"user_id không hợp lệ: {user_id}, lỗi: {e}")
            raise AuthenticationFailed(
                "Invalid user_id format", code="invalid_user_id")

        # Lấy user từ DB
        try:
            user = User.objects.get(_id=oid)
        except User.DoesNotExist:
            logger.debug(f"Không tìm thấy user với _id={oid}")
            raise AuthenticationFailed("User not found", code="user_not_found")

        logger.debug(f"Đã tìm thấy user: {user.username}")
        return user
    
    
    ### check check check check alo alo
    
    ### 12 4 5 6 7 8  9 