from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Fields to display in the list view
    list_display = ('email', 'full_name', 'user_type', 'is_verified', 'is_approved', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_approved', 'is_rejected', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'phone_number')
    ordering = ('-date_joined',)
    
    # Fields for the detail/edit view
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone_number', 'address')}),
        ('User Type', {'fields': ('user_type',)}),
        ('Verification', {'fields': ('is_verified', 'otp_hash', 'otp_created_at')}),
        ('Approval', {'fields': ('is_approved', 'approved_at', 'is_rejected', 'rejected_at', 'rejection_reason')}),
        ('Security', {'fields': ('failed_login_attempts', 'last_failed_login', 'account_locked_until')}),
        ('Processing Info', {'fields': ('processed_by', 'processed_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    # Make some fields readonly
    readonly_fields = ('date_joined', 'last_login', 'otp_hash', 'failed_login_attempts', 
                      'last_failed_login', 'account_locked_until', 'processed_at')
    
    # Actions
    actions = ['approve_users', 'reject_users', 'verify_users']
    
    def approve_users(self, request, queryset):
        """Bulk approve users"""
        from django.utils import timezone
        count = 0
        for user in queryset:
            if not user.is_approved and not user.is_rejected:
                user.is_approved = True
                user.approved_at = timezone.now()
                user.is_active = True
                user.processed_by = request.user
                user.processed_at = timezone.now()
                user.save()
                count += 1
        self.message_user(request, f'{count} users approved successfully.')
    approve_users.short_description = "Approve selected users"
    
    def reject_users(self, request, queryset):
        """Bulk reject users"""
        from django.utils import timezone
        count = 0
        for user in queryset:
            if not user.is_approved and not user.is_rejected:
                user.is_rejected = True
                user.rejected_at = timezone.now()
                user.processed_by = request.user
                user.processed_at = timezone.now()
                user.save()
                count += 1
        self.message_user(request, f'{count} users rejected.')
    reject_users.short_description = "Reject selected users"
    
    def verify_users(self, request, queryset):
        """Bulk verify users"""
        count = queryset.filter(is_verified=False).update(is_verified=True)
        self.message_user(request, f'{count} users verified.')
    verify_users.short_description = "Verify selected users"
