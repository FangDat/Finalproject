# # backend/api/authentication.py
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework_simplejwt.exceptions import AuthenticationFailed
# from .models import User
# from bson import ObjectId
# import logging

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# class CustomJWTAuthentication(JWTAuthentication):
#     """
#     Override JWTAuthentication để get_user dùng MongoDB ObjectId string.
#     """

#     def get_user(self, validated_token):
#         user_id = validated_token.get("user_id")
#         if not user_id:
#             logger.debug("Token không có user_id")
#             raise AuthenticationFailed("Token contained no user_id", code="no_user_id")

#         logger.debug(f"Token user_id: {user_id}")

#         try:
#             oid = ObjectId(user_id)
#         except Exception as e:
#             logger.debug(f"user_id không hợp lệ: {user_id}, lỗi: {e}")
#             raise AuthenticationFailed("Invalid user_id format", code="invalid_user_id")

#         try:
#             user = User.objects.get(_id=oid)
#         except User.DoesNotExist:
#             logger.debug(f"Không tìm thấy user với _id={oid}")
#             raise AuthenticationFailed("User not found", code="user_not_found")

#         logger.debug(f"Tìm thấy user: {user.username}")
#         return user

# backend/api/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken
from .models import User
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication:
    ✅ Chỉ lấy token từ cookie 'access_token'.
    """

    def authenticate(self, request):
        # -----------------
        # 1️⃣ Lấy token từ cookie
        # -----------------
        logger.debug("🔐 CustomJWTAuthentication.authenticate called")
        cookie_token = request.COOKIES.get("access_token")
        logger.debug(f"Cookie access_token: {cookie_token}")

        if not cookie_token:
            logger.debug("❌ Không tìm thấy access_token trong cookie")
            return None

        try:
            validated_token = self.get_validated_token(cookie_token)
            user = self.get_user(validated_token)
            logger.debug(f"✅ Authenticated user from cookie: {user.username}")
            return (user, validated_token)
        except InvalidToken as e:
            logger.error(f"❌ Cookie token invalid: {e}")
            raise AuthenticationFailed("Invalid token in cookie")
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý cookie token: {e}")
            raise AuthenticationFailed("Cookie token error")

    def get_user(self, validated_token):
        """
        Lấy user từ validated_token MongoDB ObjectId
        """
        user_id = validated_token.get("user_id")
        if not user_id:
            logger.error("Token không có user_id")
            raise AuthenticationFailed("Token contained no user_id", code="no_user_id")

        logger.debug(f"Token user_id: {user_id}")

        # Convert string user_id → ObjectId
        try:
            oid = ObjectId(user_id)
        except Exception as e:
            logger.error(f"user_id không hợp lệ: {user_id}, lỗi: {e}")
            raise AuthenticationFailed("Invalid user_id format", code="invalid_user_id")

        # Lấy user từ DB
        try:
            user = User.objects.get(_id=oid)
        except User.DoesNotExist:
            logger.error(f"Không tìm thấy user với _id={oid}")
            raise AuthenticationFailed("User not found", code="user_not_found")

        logger.debug(f"✅ Tìm thấy user: {user.username}")
        return user
