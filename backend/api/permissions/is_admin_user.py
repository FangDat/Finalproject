from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):  # Define custom permission class for admin users
    message = "Admin access required."

    def has_permission(self, request, view):    # Method to check if request is allowed
        user = request.user # Get current user from request
        return (     # Return True only if all conditions below are met
            user    # Ensure user object exists
            and user.is_authenticated   # Check if user is logged in
            and getattr(user, "role", "") == "admin"     # Check if user role is admin
            and getattr(user, "is_active", True)    # Ensure user account is active
        )
