import re
from rest_framework import serializers

def validate_password_strength(password):
    """
    Validate that the password meets security requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character
    """
    if len(password) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters long."
        )
    
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError(
            "Password must contain at least one uppercase letter."
        )
    
    if not re.search(r'[a-z]', password):
        raise serializers.ValidationError(
            "Password must contain at least one lowercase letter."
        )
    
    if not re.search(r'[0-9]', password):
        raise serializers.ValidationError(
            "Password must contain at least one digit."
        )
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise serializers.ValidationError(
            "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."
        )
    
    return password

def validate_username(username):
    """
    Validate that the username meets requirements:
    - At least 3 characters
    - Contains only letters, numbers, and underscores
    - Doesn't start with a number
    """
    if len(username) < 3:
        raise serializers.ValidationError(
            "Username must be at least 3 characters long."
        )
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        raise serializers.ValidationError(
            "Username must start with a letter and contain only letters, numbers, and underscores."
        )
    
    return username
