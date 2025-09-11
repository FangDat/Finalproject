# backend/api/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from .models import User

class CustomJWTAuthentication(JWTAuthentication):
    """
    Override để get_user dùng MongoDB ObjectId string
    """
    def get_user(self, validated_token):
        try:
            user_id = validated_token.get("user_id")
            if not user_id:
                raise AuthenticationFailed("Token contained no user_id", code="no_user_id")
            user = User.objects.get(_id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")
        return user
