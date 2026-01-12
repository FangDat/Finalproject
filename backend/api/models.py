from djongo import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta


class User(models.Model):
    _id = models.ObjectIdField(primary_key=True)  # MongoDB ObjectId
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_premium = models.BooleanField(default=False)

    # ✅ DÙNG TIMESTAMP (SECONDS)
    premium_started_at_ts = models.BigIntegerField(null=True, blank=True)
    premium_expires_at_ts = models.BigIntegerField(null=True, blank=True)

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
