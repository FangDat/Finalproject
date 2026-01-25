import time
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from bson import ObjectId
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from backend.api.permissions.is_admin_user import IsAdminUser


from backend.api.models import User, AdminAuditLog
from backend.api.permissions.is_admin_user import IsAdminUser

logger = logging.getLogger(__name__)


# ---------------------------
# LIST USERS
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_list_users(request):
    """
    GET /api/admin/users/
    Optional query:
      ?q=keyword   -> search by username (case-insensitive)
    """

    query = request.GET.get("q", "").strip()

    if query:
        users = User.objects.filter(username__icontains=query)
    else:
        users = User.objects.all()

    data = []
    for u in users:
        data.append({
            "user_id": str(u._id),
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "is_premium": u.is_premium,
            "created_at": u.created_at,
            "last_login_at": u.last_login_at,
        })

    return Response(data)



# ---------------------------
# USER DETAIL
# ---------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_detail(request, user_id):
    try:
        user = User.objects.get(_id=ObjectId(user_id))
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    return Response({
        "user_id": str(user._id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "is_premium": user.is_premium,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "premium_started_at_ts": user.premium_started_at_ts,
        "premium_expires_at_ts": user.premium_expires_at_ts,
    })


# ---------------------------
# BAN / UNBAN USER (SOFT DELETE)
# ---------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_ban_user(request, user_id):
    try:
        user = User.objects.get(_id=ObjectId(user_id))
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    AdminAuditLog.objects.create(
        admin_id=str(request.user._id),
        admin_username=request.user.username,    
        action="BAN_USER" if not user.is_active else "UNBAN_USER",
        target_user_id=str(user._id),
        target_username=user.username    
    )

    return Response({
        "message": "User status updated",
        "is_active": user.is_active
    })


# ---------------------------
# UPDATE PREMIUM
# ---------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_update_premium(request, user_id):
    days = int(request.data.get("days", 30))

    try:
        user = User.objects.get(_id=ObjectId(user_id))
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

    user.activate_premium(days=days)

    AdminAuditLog.objects.create(
        admin_id=str(request.user._id),
        admin_username=request.user.username,  
        action="UPDATE_PREMIUM",
        target_user_id=str(user._id),
        target_username=user.username    
    )

    return Response({
        "message": "Premium updated",
        "expires_at": user.premium_expires_at_ts
    })

@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_delete_user(request, user_id):
    """
    DELETE /api/admin/users/{id}/
    Admin delete user (hard delete)
    """

    admin_user = request.user

    try:
        target_user = User.objects.get(_id=ObjectId(user_id))
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # ❌ Không cho admin tự xoá chính mình
    if str(target_user._id) == str(admin_user._id):
        return Response(
            {"error": "Admin cannot delete itself"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Lưu info trước khi xoá để log
    target_username = target_user.username
    target_email = target_user.email

    # ❗ HARD DELETE
    target_user.delete()

    # Ghi audit log
    AdminAuditLog.objects.create(
        admin_id=str(admin_user._id),
        admin_username=admin_user.username, 
        action="DELETE_USER",
        target_user_id=str(target_user._id),
        target_username=target_username  
        # metadata={
        #     "username": target_username,
        #     "email": target_email,
        # }
    )


    return Response(
        {"message": "User deleted successfully"},
        status=status.HTTP_200_OK
    )

