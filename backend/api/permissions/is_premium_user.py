from rest_framework.permissions import BasePermission

class IsPremiumUser(BasePermission):

    message = "Premium account required to use this feature."

    def has_permission(self, request, view):    # Method to check access permission
        user = request.user # Get current user from request
        if not user or not user.is_authenticated:    # Check if user is not logged in
            return False    # Deny access if not authenticated

        return bool(getattr(user, "is_premium", False))  # Allow only if user has is_premium = True
