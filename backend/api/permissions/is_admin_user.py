from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):    # Method called when a request is made to the API
        user = request.user
        return (
            user
            and user.is_authenticated
            and getattr(user, "role", "") == "admin"    # Safely checks if user.role equals "admin"; returns False if the attribute is missing or not "admin"
            and getattr(user, "is_active", True)
        )
