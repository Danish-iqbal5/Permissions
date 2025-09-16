from rest_framework.permissions import BasePermission

class IsApprovedAndActive(BasePermission):
    message = "User is not active or not approved by admin."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_active and user.is_approved and not user.is_rejected and user.is_verified


class IsVendor(BasePermission):
    message = "Vendor access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return (user.user_type == 'vendor' and 
                user.is_fully_active() and 
                user.is_active)


class IsCustomer(BasePermission):
    message = "Customer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return (user.user_type in ['normal_customer', 'vip_customer'] and 
                user.is_fully_active() and 
                user.is_active)


class IsVIPCustomer(BasePermission):
    message = "VIP Customer access required."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return (user.user_type == 'vip_customer' and 
                user.is_fully_active() and 
                user.is_active)
