from rest_framework.permissions import BasePermission


class IsApprovedAndActive(BasePermission):
 message = "User is not active or not approved by admin."


def has_permission(self, request, view):
 user = request.user
 if not user or not user.is_authenticated:
  return False
 try:
    profile = user.profile
 except Exception:
  return False

 return user.is_active and profile.is_approved and not profile.is_rejected