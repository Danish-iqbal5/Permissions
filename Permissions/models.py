from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
from django.contrib.auth.models import User




# class UserProfile(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
#     full_name = models.CharField(max_length=255)
#     phone_number = models.CharField(max_length=15, blank=True, null=True)
#     address = models.TextField(blank=True, null=True)    
#     is_verified = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     is_approved = models.BooleanField(default=False)
#     approved_at = models.DateTimeField(blank=True, null=True)
# # Phase 1 change: store only hash
#     otp_hash = models.CharField(max_length=128, blank=True, null=True)
#     otp_created_at = models.DateTimeField(blank=True, null=True)
# # Optional: track rejections for admin filters
#     is_rejected = models.BooleanField(default=False)
#     rejected_at = models.DateTimeField(blank=True, null=True)
#     rejection_reason = models.TextField(blank=True, null=True)
    
#     # Login tracking
#     failed_login_attempts = models.IntegerField(default=0)
#     last_failed_login = models.DateTimeField(null=True, blank=True)
#     account_locked_until = models.DateTimeField(null=True, blank=True)
    
#     # Processing info
#     processed_by = models.ForeignKey(
#         User, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True, 
#         related_name='processed_profiles'
#     )
#     processed_at = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return self.user.username
        
#     def increment_login_attempts(self):
#         """Increment failed login attempts and implement exponential backoff"""
#         self.failed_login_attempts += 1
#         self.last_failed_login = timezone.now()
        
#         # Lock account temporarily if too many failed attempts
#         if self.failed_login_attempts >= 5:
#             # Calculate lockout duration: 5min, 15min, 30min, 1hr, 2hr...
#             minutes = min(120, 5 * (2 ** (self.failed_login_attempts - 5)))
#             self.account_locked_until = timezone.now() + timedelta(minutes=minutes)
        
#         self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
#     def reset_login_attempts(self):
#         """Reset failed login attempts after successful login"""
#         self.failed_login_attempts = 0
#         self.last_failed_login = None
#         self.account_locked_until = None
#         self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])



class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
       ('admin', 'Admin'),
       ('vendor', 'Vendor'),
       ('vip_customer', 'VIP Customer'),
       ('normal_customer', 'Normal Customer'), 
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')

    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    otp_hash = models.CharField(max_length=128, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    is_rejected = models.BooleanField(default=False)
    rejected_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)

    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_profiles'
    )
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def is_fully_active(self):
        """Check if user can access platform."""
        if self.user_type == 'normal_customer':
            return self.is_verified
        else:
            return self.is_verified and self.is_approved
    
    def increment_login_attempts(self):
        """Increment failed login attempts and implement exponential backoff"""
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        if self.failed_login_attempts >= 5:
            minutes = min(120, 5 * (2 ** (self.failed_login_attempts - 5)))
            self.account_locked_until = timezone.now() + timedelta(minutes=minutes)
        
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
    
    def reset_login_attempts(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.account_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
