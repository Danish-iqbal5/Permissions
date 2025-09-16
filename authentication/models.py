from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission


class User(AbstractUser):
    USER_TYPE_CHOICES = [
       ('admin', 'Admin'),
       ('vendor', 'Vendor'),
       ('vip_customer', 'VIP Customer'),
       ('normal_customer', 'Normal Customer'), 
    ]
    
    # Override the default username field to use email
    username = None
    email = models.EmailField(unique=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='normal_customer')
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
    
    # Processing info
    processed_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_users'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    
   
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    def __str__(self):
        return self.email

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
