# Python standard library imports
from datetime import timedelta

# Django imports
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

# Third-party imports
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Local application imports
from .models import UserProfile
from .permissions import IsApprovedAndActive
from .serializers import (
    AdminDecisionSerializer,
    PasswordSetSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from .throttles import (
    LoginRateThrottle,
    OTPVerifyRateThrottle,
    ResendOTPThrottle,
)
from .utils import (
    generate_and_send_otp,
    send_mail,
    verify_otp,
)


# ============================================================
# Authentication Views
# ============================================================

class ResendOTPView(APIView):
    """
    Endpoint for resending OTP to user's email.
    
    Allows users to request a new OTP if the previous one expired or was not received.
    Rate limited to prevent abuse.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ResendOTPThrottle]

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Resend OTP",
        operation_description="Request a new OTP code to be sent to your email",
        request_body=ResendOTPSerializer,
        responses={
            200: openapi.Response("OTP sent successfully"),
            404: openapi.Response("User not found"),
            429: openapi.Response("Too many requests"),
        }
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except (User.DoesNotExist, ObjectDoesNotExist):
            return Response({"error": "User not found."}, status=404)
            
        otp_hash, otp_created_at = generate_and_send_otp(email)
        profile.otp_hash = otp_hash
        profile.otp_created_at = otp_created_at
        profile.save(update_fields=["otp_hash", "otp_created_at"])
        
        return Response({"message": "OTP resent to your email."}, status=200)

class ApprovedUserTokenObtainPairView(TokenObtainPairView):
    """
    Enhanced login endpoint that checks user approval status.
    
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    Only works for approved and active users.
    """
    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Login for approved users",
        operation_description="Authenticate and get JWT tokens. Only works for approved users.",
        responses={
            200: openapi.Response("Login successful with JWT tokens"),
            403: openapi.Response("Account not approved or inactive"),
            404: openapi.Response("User not found"),
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            try:
                user = User.objects.get(username=request.data['username'])
                profile = user.profile
                if not profile.is_approved or not user.is_active:
                    return Response({
                        "error": "Your account is not yet approved or is inactive."
                    }, status=403)
            except (User.DoesNotExist, ObjectDoesNotExist):
                return Response({
                    "error": "User not found"
                }, status=404)
        return response
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Logout user",
        operation_description="Blacklist the current refresh token to prevent its future use",
        responses={
            200: openapi.Response("Successfully logged out"),
            400: openapi.Response("Invalid token")
        }
    )
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                "message": "Successfully logged out."
            }, status=200)
        except Exception as e:
            return Response({
                "error": "Invalid token."
            }, status=400)

# ============================================================
# Admin Views
# ============================================================

class AdminDashboardRequestApprovalView(APIView):
    """
    Admin dashboard for managing user approval requests.
    
    Provides endpoints for:
    - Listing all pending user approval requests
    - Approving or rejecting user registrations
    
    Only accessible by staff users (administrators).
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        tags=["Admin"],
        operation_summary="List pending user approvals",
        operation_description="Returns a list of all users who have verified their email but are pending admin approval",
        responses={
            200: openapi.Response(
                description="List of pending users",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        }
                    )
                )
            ),
            403: openapi.Response("Not an admin")
        }
    )
    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
        
        # Get all pending users (verified but not approved/rejected)
        pending_users = UserProfile.objects.filter(
            is_verified=True,
            is_approved=False,
            is_rejected=False
        ).select_related('user')
        
        users_data = []
        for profile in pending_users:
            users_data.append({
                'id': profile.id,
                'username': profile.user.username,
                'email': profile.user.email,
                'full_name': profile.full_name,
                'created_at': profile.created_at,
            })
        
        return Response(users_data, status=200)

    @swagger_auto_schema(
        tags=["Admin"],
        request_body=AdminDecisionSerializer,
        responses={
            200: openapi.Response("User approved/rejected successfully"),
            400: openapi.Response("Invalid request"),
            403: openapi.Response("Not an admin"),
            404: openapi.Response("User not found")
        }
    )
    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
            
        serializer = AdminDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['id']
        action = serializer.validated_data['action']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        try:
            profile = UserProfile.objects.select_related('user').get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
            
        if profile.is_approved or profile.is_rejected:
            return Response({"error": "User already processed"}, status=400)
            
        if action == 'approve':
            profile.is_approved = True
            profile.approved_at = timezone.now()
            profile.user.is_active = True
            message = "Your account has been approved. You can now set your password."
        else:  # action == 'reject'
            profile.is_rejected = True
            profile.rejected_at = timezone.now()
            profile.rejection_reason = rejection_reason
            message = f"Your account has been rejected. Reason: {rejection_reason}" if rejection_reason else "Your account has been rejected."
            
        profile.processed_by = request.user
        profile.processed_at = timezone.now()
        profile.user.save()
        profile.save()
        
        # Send email notification to user
        send_mail(
            subject="Account Status Update",
            message=message,
            from_email='Danish@Bussines.com',
            recipient_list=[profile.user.email],
            fail_silently=False
        )
        
        return Response({
            "message": f"User has been {action}d successfully"
        }, status=200)






# ============================================================
# Registration Views
# ============================================================

class RegisterView(APIView):
    """
    User registration endpoint.
    
    Creates a new user account and sends an OTP for email verification.
    The user will need to:
    1. Verify their email using the OTP
    2. Wait for admin approval
    3. Set their password
    before they can log in.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Register new user",
        operation_description="Create a new user account and receive OTP for verification",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response("OTP sent to email"),
            400: openapi.Response("Email or username already in use")
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        full_name = serializer.validated_data['full_name']

        # Check for existing users
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use."}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already in use."}, status=400)

        # Create user account (inactive until approved)
        user = User.objects.create_user(username=username, email=email)
        user.is_active = False
        user.save()

        # Create user profile and send OTP
        profile = UserProfile.objects.create(user=user, full_name=full_name)
        otp_hash, otp_created_at = generate_and_send_otp(profile.user.email)
        profile.otp_hash = otp_hash
        profile.otp_created_at = otp_created_at
        profile.save(update_fields=["otp_hash", "otp_created_at"])

        return Response({"message": "OTP sent to your email."}, status=201)



# ============================================================
# Verification Views
# ============================================================

class VerifyOTPView(APIView):
    """
    OTP verification endpoint.
    
    Verifies the OTP sent to user's email during registration.
    After successful verification:
    1. User's email is marked as verified
    2. User awaits admin approval
    3. OTP hash is cleared from database
    
    Rate limited to prevent brute force attempts.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyRateThrottle]

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Verify OTP",
        operation_description="Verify the OTP code sent to your email",
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response("OTP verified successfully"),
            400: openapi.Response("Invalid or expired OTP"),
            404: openapi.Response("User not found")
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
            profile = user.profile
        except (User.DoesNotExist, ObjectDoesNotExist):
            return Response({"error": "Invalid email or user not found."}, status=404)

        if not profile.otp_hash or not profile.otp_created_at:
            return Response({"error": "No OTP set for this user."}, status=400)

        # Check OTP validity and expiry
        if not verify_otp(otp_input, profile.otp_hash, profile.otp_created_at):
            return Response({"error": "Invalid or expired OTP."}, status=400)

        profile.is_verified = True
        profile.otp_hash = None
        profile.save(update_fields=["is_verified", "otp_hash"])

        return Response({"message": "OTP verified successfully."}, status=200)




# ============================================================
# Password Management Views
# ============================================================

class SetPasswordView(APIView):
    """
    Password setup endpoint for approved users.
    
    Allows users to set their initial password after:
    1. Email verification is complete
    2. Admin has approved their account
    
    The user can only access this endpoint once to set their initial password.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["Auth"],
        operation_summary="Set initial password",
        operation_description="Set your password after admin approval",
        request_body=PasswordSetSerializer,
        responses={
            200: openapi.Response("Password set successfully"),
            403: openapi.Response("User not approved/active"),
            404: openapi.Response("User not found")
        }
    )
    def post(self, request, user_id):
        s = PasswordSetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        password = s.validated_data['password']
        
        try:
            profile = UserProfile.objects.select_related('user').get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        user = profile.user
        if not user.is_active or not profile.is_approved or profile.is_rejected:
            return Response({"error": "User is not approved/active."}, status=403)

        user.password = make_password(password)
        user.save(update_fields=["password"])
        
        return Response({"message": "Password set successfully. You can now log in."}, status=200)