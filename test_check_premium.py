# test_check_premium.py
import os
import django
import logging

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.myproject.settings')
django.setup()

from rest_framework_simplejwt.authentication import JWTAuthentication
from backend.api.authentication import CustomJWTAuthentication

# Token người dùng đưa vào (Access token vừa lấy từ login)
USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3Njc4MzcxLCJqdGkiOiJhMjRjYmM2YTg2ZmY0NDA2OWRiY2NjNGJmYWMxMzY3ZCIsInVzZXJfaWQiOiI2OGMzZjBhNDczMDM5YThiNzZiMzViNzcifQ.wxjAi2-dvJaCJdqrGgeBdrnZWEP5UApUuzf_7G6fa9E"

def test_check_premium(token):
    auth = CustomJWTAuthentication()
    try:
        validated_token = auth.get_validated_token(token)
        print("=== Token hợp lệ ===")
        print("user_id trong token:", validated_token.get("user_id"))

        user = auth.get_user(validated_token)
        print("=== User tìm được từ token ===")
        print(f"username: {user.username}, user_id: {user.id}, is_premium: {user.is_premium}")

    except Exception as e:
        print("FAILED: Token invalid or expired")
        print("Details:", e)

if __name__ == "__main__":
    test_check_premium(USER_TOKEN)
