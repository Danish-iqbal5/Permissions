
from django.utils import timezone


from django.contrib import admin
from django.utils.timezone import now
from django.core.mail import send_mail
from django.conf import settings

from .models import User
# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_verified', 'is_active', 'approved_at')
    list_filter = ('is_verified', 'is_active')
    search_fields = ('email', 'username')
    actions = ['approve_selected_users']

    def approve_selected_users(self, request, queryset):
        users_to_approve = queryset.filter(is_verified=True, is_active=False)
        count = 0
        for user in users_to_approve:
            user.is_active = True
            user.approved_at = now()
            user.save()
            count += 1

            # Send email with password setup link
            set_password_url = f"http://localhost:8000/set-password/{user.id}/"  # Change for production
            send_mail(
                subject="Your account has been approved!",
                message=f"Hi {user.username}, your account is approved. Set your password here: {set_password_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        self.message_user(request, f"{count} user(s) approved and notified.")

    approve_selected_users.short_description = "Approve and activate selected users"

# @admin.register(AdminDashboardRequestApproval)
# class AdminDashboardRequestApprovalAdmin(admin.ModelAdmin):
#     list_display = ('pending_user_username', 'pending_user_email', 'requested_at', 'is_approved', 'approved_at')
#     list_filter = ('is_approved',)
#     search_fields = ('pending_user__username', 'pending_user__email')
#     actions = ['approve_selected_users']

#     def pending_user_email(self, obj):
#         return obj.pending_user.email

#     def pending_user_username(self, obj):
#         return obj.pending_user.username

#     pending_user_email.short_description = 'Email'
#     pending_user_username.short_description = 'Username'

#     def approve_selected_users(self, request, queryset):
#         updated = 0
#         for obj in queryset.filter(is_approved=False):
#             obj.is_approved = True
#             obj.approved_at = timezone.now()
#             obj.save()
#             updated += 1
#         self.message_user(request, f"{updated} user(s) approved successfully.")

#     approve_selected_users.short_description = "Approve selected pending users"
