import re
from rest_framework import serializers
from .models import User
from .validators import validate_password_strength, validate_username
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone_number', 'address', 'user_type',
                 'is_verified', 'is_approved', 'approved_at', 'is_rejected', 
                 'rejected_at', 'rejection_reason']


USER_TYPE_CHOICES = [
    ('normal_customer', 'Normal Customer'),
    ('vip_customer', 'VIP Customer'),
    ('vendor', 'Vendor'),
]

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    user_type = serializers.ChoiceField(choices=USER_TYPE_CHOICES, default='normal_customer')

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(
        min_length=6, 
        max_length=6,
        error_messages={
            'min_length': 'OTP must be exactly 6 digits.',
            'max_length': 'OTP must be exactly 6 digits.'
        }
    )
    
    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class AdminDecisionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    action = serializers.ChoiceField(
        choices=['approve', 'reject'],
        error_messages={
            'invalid_choice': 'Action must be either "approve" or "reject".'
        }
    )
    rejection_reason = serializers.CharField(
        allow_blank=True, 
        required=False,
        max_length=500
    )

    def validate(self, data):
        if data.get('action') == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError(
                {"rejection_reason": "Rejection reason is required when rejecting a user."}
            )
        return data

class PasswordSetSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

class ForgotPasswordSerializer(serializers.Serializer):
    """Request a password reset by providing email."""
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    """Reset password using OTP and new password."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
