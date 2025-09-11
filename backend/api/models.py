from djongo import models
from django.contrib.auth.hashers import make_password
from django.utils import timezone


class User(models.Model):
    _id = models.ObjectIdField(primary_key=True)  # MongoDB ObjectId
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    is_premium = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def id(self):
        # SimpleJWT cần user.id -> trả str
        return str(self._id)


class RevokedToken(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    jti = models.CharField(max_length=200, unique=True)
    token = models.TextField(blank=True, null=True)
    user_id = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"RevokedToken(jti={self.jti}, user={self.user_id})"
