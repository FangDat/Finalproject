from rest_framework.permissions import BasePermission

class IsPremiumUser(BasePermission):
    """
    Chỉ cho phép user có is_premium = True
    """

    message = "Premium account required to use this feature."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(getattr(user, "is_premium", False))
