from djongo import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
import time



class User(models.Model):
    _id = models.ObjectIdField(primary_key=True)  # MongoDB ObjectId
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_premium = models.BooleanField(default=False)
    
    role = models.CharField(
        max_length=20,
        default="user"   # user | admin
    )

    is_active = models.BooleanField(default=True)

    created_at = models.BigIntegerField(
        default=lambda: int(time.time())
    )

    last_login_at = models.BigIntegerField(
        null=True,
        blank=True
    )
    
    

    # ✅ DÙNG TIMESTAMP (SECONDS)
    premium_started_at_ts = models.BigIntegerField(null=True, blank=True)
    premium_expires_at_ts = models.BigIntegerField(null=True, blank=True)
    
    # =========================
    # BILLING INFORMATION (INTERNAL)
    # =========================
    billing_first_name = models.CharField(max_length=100, null=True, blank=True)
    billing_last_name = models.CharField(max_length=100, null=True, blank=True)
    billing_address_line1 = models.CharField(max_length=255, null=True, blank=True)
    billing_city = models.CharField(max_length=100, null=True, blank=True)
    billing_postal_code = models.CharField(max_length=20, null=True, blank=True)
    billing_phone = models.CharField(max_length=30, null=True, blank=True)

    billing_completed = models.BooleanField(default=False)
     # =========================
    # STRIPE
    # =========================
    stripe_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    # =========================
    # PREMIUM HELPERS
    # =========================
    def activate_premium(self, days=30):
        now = timezone.now()
        now_ts = int(now.timestamp())
        expires_ts = int((now + timedelta(days=days)).timestamp())

        self.is_premium = True
        self.premium_started_at_ts = now_ts
        self.premium_expires_at_ts = expires_ts

        self.save(update_fields=[
            "is_premium",
            "premium_started_at_ts",
            "premium_expires_at_ts"
        ])

    def deactivate_premium(self):
        self.is_premium = False
        self.save(update_fields=["is_premium"])

    def __str__(self):
        return self.username

    @property
    def id(self):
        return str(self._id)

    @property
    def is_authenticated(self):
        return True


class RevokedToken(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    jti = models.CharField(max_length=200, unique=True)
    token = models.TextField(blank=True, null=True)
    user_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"RevokedToken(jti={self.jti}, user={self.user_id})"

# -----------------------------
# SearchHistory Model (update)
# -----------------------------
class SearchHistory(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    user_id = models.CharField(max_length=200)
    city_name = models.CharField(max_length=200)
    lat = models.FloatField(null=True, blank=True)   # thêm field lat
    lon = models.FloatField(null=True, blank=True)   # thêm field lon
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.city_name} ({self.lat},{self.lon}) for {self.user_id}"

class AdminAuditLog(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    admin_id = models.CharField(max_length=200)
    admin_username = models.CharField(max_length=150, null=True, blank=True) 
    action = models.CharField(max_length=100)
    target_user_id = models.CharField(max_length=200, null=True, blank=True)
    target_username = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.BigIntegerField(
        default=lambda: int(time.time())
    )

    def __str__(self):
        return f"{self.action} by {self.admin_id}"
