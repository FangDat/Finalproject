from rest_framework.permissions import BasePermission

class IsPremiumUser(BasePermission):
    """
    Chỉ cho phép user có is_premium=True truy cập.
    Hiện tại tất cả mặc định False, sau này sẽ update khi thanh toán thành công.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        # Tạm mặc định False để test
        return getattr(user, 'is_premium', False)
