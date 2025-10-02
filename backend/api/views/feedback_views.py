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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@api_view(['POST'])
@permission_classes([AllowAny])  # cho phép user đã login hay chưa đều gửi
def send_feedback(request):
    """
    Nhận feedback từ frontend và gửi email đến admin.
    """
    message = request.data.get("message", "").strip()
    email = request.data.get("email", "").strip()

    if not message:
        return Response({"error": "Message is required"}, status=400)

    subject = f"VietCloud Feedback from {email or 'Anonymous'}"
    body = f"Support message from user:\n\n{message}\n\nSender email: {email or 'Anonymous'}"

    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,            # địa chỉ gửi đi
            ["datpvgcd220073@fpt.edu.vn"],       # địa chỉ nhận (thay bằng email admin)
            fail_silently=False,
        )
        return Response({"message": "Feedback sent successfully"})
    except Exception as e:
        logger.error(f"Send feedback mail failed: {e}")
        return Response({"error": "Unable to send email"}, status=500)
