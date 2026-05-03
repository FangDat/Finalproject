from rest_framework.permissions import BasePermission

class IsPremiumUser(BasePermission):
    """
    Chỉ cho phép user có is_premium = True
    """

    message = "Premium account required to use this feature."

    def has_permission(self, request, view):    # Method called by the permission system to determine if the incoming request is allowed to access the view
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return bool(getattr(user, "is_premium", False)) # Safely get user's is_premium flag (default False if missing) and ensure a boolean result
