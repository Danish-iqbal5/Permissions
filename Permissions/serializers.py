from rest_framework import serializers
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
 

    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'username', 'is_active', 'full_name', 'phone_number', 'address']