from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta

from .models import UserProfile
from .utils import send_otp_email, send_password_setup_email
from .serializers import UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')

        if not all([username, email]):
            return Response({"error": "Username and email are required."}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use."}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already in use."}, status=400)

        # Create user without password for now
        user = User.objects.create_user(username=username, email=email)
        user.is_active = False
        user.save()

        # Generate and send OTP
        otp = send_otp_email(email)

        # Create user profile with optional fields blank
        UserProfile.objects.create(
            user=user,
            otp=otp,
            otp_created_at=timezone.now()
        )

        return Response({"message": "OTP sent to your email."}, status=201)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not all([email, otp]):
            return Response({"error": "Email and OTP are required."}, status=400)

        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except (User.DoesNotExist, ObjectDoesNotExist):
            return Response({"error": "Invalid email or user not found."}, status=404)

        if profile.otp != otp:
            return Response({"error": "Invalid OTP."}, status=400)

        if profile.otp_created_at and (timezone.now() - profile.otp_created_at > timedelta(minutes=10)):
            return Response({"error": "OTP expired."}, status=400)

        profile.is_verified = True
        profile.otp = None
        profile.save(update_fields=["is_verified", "otp"])

        return Response({"message": "OTP verified successfully."}, status=200)


class AdminDashboardRequestApprovalView(APIView):
    def get(self, request):
        users = UserProfile.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def patch(self, request):
        user_profile_id = request.data.get('id')

        try:
            profile = UserProfile.objects.get(id=user_profile_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=404)

        if not profile.is_verified:
            return Response({"error": "User is not verified yet."}, status=400)

        user = profile.user
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

            profile.is_approved = True
            profile.approved_at = timezone.now()
            profile.save(update_fields=["is_approved", "approved_at"])

            set_password_url = f"http://localhost:8000/set-password/{profile.id}/"
            send_password_setup_email(user.email, set_password_url)

        return Response({"message": "User approved and password setup email sent."}, status=200)


class SetPasswordView(APIView):
    def post(self, request, user_id):
        password = request.data.get("password")

        if not password:
            return Response({"error": "Password is required."}, status=400)

        try:
            profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        user = profile.user
        if not user.is_active or not profile.is_approved:
            return Response({"error": "User is not approved or active."}, status=403)

        # Set and hash the new password
        user.password = make_password(password)
        user.save(update_fields=["password"])

        return Response({"message": "Password set successfully. You can now log in."}, status=200)
