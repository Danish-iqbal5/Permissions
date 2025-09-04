# from rest_framework import serializers
# from .models import UserProfile


# class UserSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(source='user.email', read_only=True)
#     username = serializers.CharField(source='user.username', read_only=True)
#     is_active = serializers.BooleanField(source='user.is_active', read_only=True)
 

#     class Meta:
#         model = UserProfile
#         fields = ['id', 'email', 'username', 'is_active', 'full_name', 'phone_number', 'address']



from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile  


class UserSerializer(serializers.ModelSerializer):
  username = serializers.CharField(source='user.username')
  email = serializers.EmailField(source='user.email')


class Meta:
  model = UserProfile
  fields = ['id', 'username', 'email', 'full_name', 'phone_number', 'address', 'is_verified', 'is_approved', 'approved_at', 'is_rejected', 'rejected_at', 'rejection_reason']




class RegisterSerializer(serializers.Serializer):
  username = serializers.CharField()
  email = serializers.EmailField()
  full_name = serializers.CharField()




class VerifyOTPSerializer(serializers.Serializer):
  email = serializers.EmailField()
  otp = serializers.CharField(max_length=6)




class ResendOTPSerializer(serializers.Serializer):
  email = serializers.EmailField()




class AdminDecisionSerializer(serializers.Serializer):
  id = serializers.IntegerField()
  action = serializers.ChoiceField(choices=['approve', 'reject'])
  rejection_reason = serializers.CharField(allow_blank=True, required=False)




class PasswordSetSerializer(serializers.Serializer):
  password = serializers.CharField(min_length=8)        