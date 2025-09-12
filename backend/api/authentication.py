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
    Override JWTAuthentication để get_user dùng MongoDB ObjectId string.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            logger.debug("Token không có user_id")
            raise AuthenticationFailed("Token contained no user_id", code="no_user_id")

        logger.debug(f"Token user_id: {user_id}")

        try:
            oid = ObjectId(user_id)
        except Exception as e:
            logger.debug(f"user_id không hợp lệ: {user_id}, lỗi: {e}")
            raise AuthenticationFailed("Invalid user_id format", code="invalid_user_id")

        try:
            user = User.objects.get(_id=oid)
        except User.DoesNotExist:
            logger.debug(f"Không tìm thấy user với _id={oid}")
            raise AuthenticationFailed("User not found", code="user_not_found")

        logger.debug(f"Tìm thấy user: {user.username}")
        return user
