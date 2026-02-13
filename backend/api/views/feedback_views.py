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
import resend
import threading
from django.conf import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ==============================
# RESEND ASYNC EMAIL SENDER
# ==============================
def send_mail_async_feedback(subject, message, recipient_list):
    def task():
        try:
            resend.api_key = settings.RESEND_API_KEY

            html_content = message.replace("\n", "<br>")

            for recipient in recipient_list:
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": recipient,
                    "subject": subject,
                    "html": f"""
                        <div style="font-family:Arial,sans-serif;padding:20px">
                            <h2>{subject}</h2>
                            <p>{html_content}</p>
                        </div>
                    """
                })

            logger.debug("✅ Feedback email sent via Resend")

        except Exception as e:
            logger.exception(f"❌ Resend feedback email failed: {str(e)}")

    threading.Thread(target=task).start()


@api_view(['POST'])
@permission_classes([AllowAny]) 
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
        send_mail_async_feedback(
            subject,
            body,
            ["skyfall20192k4@gmail.com"]  # email admin
        )
        return Response({"message": "Feedback sent successfully"})
    except Exception as e:
        logger.error(f"Send feedback mail failed: {e}")
        return Response({"error": "Unable to send email"}, status=500)
