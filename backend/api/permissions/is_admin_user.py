from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):
        user = request.user
        return (
            user
            and user.is_authenticated
            and getattr(user, "role", "") == "admin"
            and getattr(user, "is_active", True)
        )
