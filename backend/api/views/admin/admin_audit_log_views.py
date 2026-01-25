from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from backend.api.permissions.is_admin_user import IsAdminUser
from backend.api.models import AdminAuditLog


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_audit_log_list(request):
    """
    View admin audit logs (latest first)
    """
    logs = AdminAuditLog.objects.all().order_by("-created_at")[:200]

    data = []
    for log in logs:
        data.append({
            "log_id": str(log._id),
            "admin_id": log.admin_id,
            "action": log.action,
            "target_user_id": log.target_user_id,
            "created_at": log.created_at,
            "admin_username": log.admin_username or log.admin_id,
            "target_username": log.target_username,
            "created_at_ts": log.created_at,
        })

    return Response(data)
