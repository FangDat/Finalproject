# test_get_user.py
import os
import sys
import django
import logging

# Thêm backend vào sys.path nếu cần
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Thiết lập Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")  # <-- sửa đường dẫn settings.py của bạn
django.setup()

from backend.api.authentication import CustomJWTAuthentication
from backend.api.models import User
from rest_framework_simplejwt.exceptions import AuthenticationFailed

# Logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_get_user(token_str):
    auth = CustomJWTAuthentication()

    print("\n=== Bước 1: Token người dùng đưa vào ===")
    print(token_str)

    try:
        validated_token = auth.get_validated_token(token_str)
        print("\n=== Bước 2: Token hệ thống xác thực ===")
        print(validated_token)

        user = auth.get_user(validated_token)
        print("\n=== Bước 3: User tìm được từ token ===")
        print(f"username: {user.username}, user_id: {user._id}")

    except AuthenticationFailed as e:
        print("\n=== AuthenticationFailed ===")
        print(e)

if __name__ == "__main__":
    # Dán token của user "c" vào đây
    token_from_user = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3Njc4MzcxLCJqdGkiOiJhMjRjYmM2YTg2ZmY0NDA2OWRiY2NjNGJmYWMxMzY3ZCIsInVzZXJfaWQiOiI2OGMzZjBhNDczMDM5YThiNzZiMzViNzcifQ.wxjAi2-dvJaCJdqrGgeBdrnZWEP5UApUuzf_7G6fa9E"
    test_get_user(token_from_user)


#check check check