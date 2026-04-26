import requests
import datetime
from urllib.parse import quote
import logging
import re
import stripe
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
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from bson import ObjectId


from ..permissions import IsPremiumUser
from ..models import User
from ..serializers import UserSerializer
from ..authentication import CustomJWTAuthentication

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stripe.api_key = settings.STRIPE_SECRET_KEY_TEST

def get_or_create_stripe_customer(user: User):   # Function to get or create Stripe customer
    """
    OpenWeather-style:
    - 1 user = 1 Stripe customer
    """
    if user.stripe_customer_id: # Check if user already has Stripe ID
        return user.stripe_customer_id  # Return existing ID

    customer = stripe.Customer.create(   # Create new Stripe customer
        email=user.email,    # Set customer email
        name=f"{user.billing_first_name} {user.billing_last_name}",
        phone=user.billing_phone,
        address={
            "line1": user.billing_address_line1,
            "city": user.billing_city,
            "postal_code": user.billing_postal_code,
        },
        metadata={  # Attach metadata
            "user_id": str(user._id),   # Store user ID
            "username": user.username,  # Store username
        }
    )

    user.stripe_customer_id = customer.id   # Save Stripe customer ID
    user.save(update_fields=["stripe_customer_id"]) # Update only this field

    return customer.id # Return new customer ID


# ============================
# MOCK PAYMENT SUCCESS
# ============================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_success_mock(request):
    """
    Tạm thời dùng để giả lập Stripe payment success
    Sau này Stripe webhook chỉ cần gọi lại logic này
    """
    user = request.user

    # Activate premium 30 days
    user.activate_premium(days=30)

    return Response({
        "message": "Payment successful. Premium activated.",
        "is_premium": True,
        "premium_expires_at_ts": user.premium_expires_at_ts
    }, status=200)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])  
def create_checkout_session(request):   # Create Stripe checkout session
    user = request.user # Get current user

    # 🔒 BLOCK ACTIVE PREMIUM USER
    if getattr(user, "is_premium", False):    # Check if already premium
        return Response(
            {"error": "You are not due for the next payment yet."},
            status=400
        )

    # 🔒 HARD CHECK BILLING INFO
    if not getattr(user, "billing_completed", False):    # Check billing info
        return Response(
            {"error": "Billing information required"},
            status=400
        )

    try:
        # 1️⃣ Ensure Stripe Customer
        stripe_customer_id = get_or_create_stripe_customer(user)     # Ensure Stripe customer

        # 2️⃣ Create Checkout Session WITH INVOICE
        session = stripe.checkout.Session.create(    # Create checkout session
            mode="payment",
            customer=stripe_customer_id,
            payment_method_types=["card"],
            invoice_creation={"enabled": True},  #  KEY POINT
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "VietCloud Premium (30 days)",
                    },
                    "unit_amount": 299,  # $6.96
                },
                "quantity": 1,
            }],
            success_url="http://localhost:8080/#/?payment=success",
            cancel_url="http://localhost:8080/#/",
            client_reference_id=str(user._id),  # Attach user ID
        )

        return Response({   # Return session URL
            "checkout_url": session.url
        }, status=200)

    except Exception as e:  # Catch error
        logger.exception("Create checkout session failed")
        return Response({"error": str(e)}, status=500)



@csrf_exempt     # Disable CSRF protection for this endpoint (Stripe requires it)
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow any request (Stripe server calls this)
def stripe_webhook(request):     # Handle Stripe webhook events
    payload = request.body  # Get raw request body from Stripe
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")  # Get Stripe signature header
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET_TEST # Load webhook secret key

    # ----------------------------
    # 1. Verify signature
    # ----------------------------
    try:    # Try to verify webhook signature
        event = stripe.Webhook.construct_event( # Construct Stripe event safely
            payload=payload,    # Raw payload data
            sig_header=sig_header,    # Signature from header
            secret=endpoint_secret, # Secret for validation
        )
    except ValueError:  # Invalid payload error
        logger.error("Stripe webhook invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError: # Invalid signature error
        logger.error("Stripe webhook invalid signature")
        return HttpResponse(status=400)

    event_type = event["type"]  # Extract event type from Stripe
    logger.info(f"[Stripe Webhook] Event received: {event_type}")

    # ----------------------------
    # 2. Handle event
    # ----------------------------
    if event_type == "checkout.session.completed":  # Check if payment completed
        session = event["data"]["object"]    # Get session object

        user_id = session.get("client_reference_id")    # Get user_id from metadata
        logger.info(f"Checkout completed for user_id={user_id}")    # Log user id

        if not user_id:
            logger.warning("Stripe session missing client_reference_id")
            return HttpResponse(status=200)

        try:     # Try to find user
            user = User.objects.get(_id=ObjectId(user_id))   # Get user by ObjectId
            user.activate_premium(days=30)  

            logger.info(
                f"✅ Premium activated for user={user.username} "
                f"until_ts={user.premium_expires_at_ts}"
            )

        except User.DoesNotExist:   # If user not found
            logger.error(f"❌ User not found for ObjectId={user_id}")

        except Exception as e:   # Catch any other errors
            logger.exception("❌ Failed to activate premium")

    elif event_type in [    # Handle ignored events
        "payment_intent.created",
        "payment_intent.succeeded",
        "charge.succeeded",
        "charge.updated",
    ]:
        logger.debug(f"Ignored Stripe event: {event_type}") # Log ignored events

    else:
        logger.debug(f"Unhandled Stripe event: {event_type}")   

    return HttpResponse(status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Require authenticated user
def get_billing_info(request): # Get user billing information
    user = request.user # Get current user

    return Response({   # Return billing data
        "first_name": user.billing_first_name,
        "last_name": user.billing_last_name,
        "address_line1": user.billing_address_line1,
        "city": user.billing_city,
        "postal_code": user.billing_postal_code,
        "phone": user.billing_phone,
        "billing_completed": bool(user.billing_completed),
    }, status=200)

@api_view(['POST'])  # Define POST endpoint
@permission_classes([IsAuthenticated])
def save_billing_info(request):  # Save billing information
    user = request.user # Get current user
    data = request.data # Get request data

    # --------------------
    # REQUIRED FIELDS
    # --------------------
    required_fields = [
        "first_name",
        "last_name",
        "address_line1",
        "city",
        "postal_code",
        "phone",
    ]

    for field in required_fields:    # Loop through required fields
        if not data.get(field): # Check if missing
            return Response(
                {"error": f"{field} is required"},
                status=400
            )

    # --------------------
    # VALIDATION RULES
    # --------------------
    # VN Postal Code: 6 digits
    if not re.match(r"^\d{6}$", data["postal_code"]):
        return Response(
            {"error": "Postal code must be 6 digits"},
            status=400
        )

    # VN Phone: +84xxxxxxxxx
    if not re.match(r"^\+\d{11}$", data["phone"]):
        return Response(
            {"error": "Phone must be in format +xxxxxxxxxxx"},
            status=400
        )

    # --------------------
    # SAVE
    # --------------------
    user.billing_first_name = data["first_name"]     # Save first name
    user.billing_last_name = data["last_name"]
    user.billing_address_line1 = data["address_line1"]
    user.billing_city = data["city"]
    user.billing_postal_code = data["postal_code"]
    user.billing_phone = data["phone"]
    user.billing_completed = True

    user.save(update_fields=[   # Save only specific fields
        "billing_first_name",
        "billing_last_name",
        "billing_address_line1",
        "billing_city",
        "billing_postal_code",
        "billing_phone",
        "billing_completed",
    ])

    return Response(
        {"message": "Billing information saved"},
        status=200
    )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])   # Require authentication
def list_stripe_invoices(request):  # List Stripe invoices
    user = request.user  # Get current user

    if not user.stripe_customer_id:  # If user has no Stripe customer
        return Response([], status=200)

    try:
        invoices = stripe.Invoice.list( # Call Stripe API
            customer=user.stripe_customer_id,   # Filter by customer
            limit=20    # Limit results
        )

        result = []  # Initialize result list

        for inv in invoices.auto_paging_iter(): # Iterate invoices
            result.append({ # Add invoice data
                "invoice_number": inv.number,
                "amount": f"{inv.amount_paid / 100:.2f} {inv.currency.upper()}",
                "created_at": datetime.datetime.utcfromtimestamp(
                    inv.created
                ).strftime("%H:%M:%S %b %d, %Y UTC"),
                "hosted_invoice_url": inv.hosted_invoice_url,
                "status": inv.status,  # Invoice status
            })

        return Response(result, status=200) # Return invoice list

    except Exception as e:
        logger.exception("List invoice failed")
        return Response({"error": str(e)}, status=500)

