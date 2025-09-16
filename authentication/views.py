import traceback
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import User
from .permissions import IsApprovedAndActive
from .serializers import (
    AdminDecisionSerializer,
    ForgotPasswordSerializer,
    PasswordSetSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
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
    send_password_setup_email,
    verify_otp,
)


# Authentication Views

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendOTPThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
            
        otp_hash, otp_created_at = generate_and_send_otp(email)
        user.otp_hash = otp_hash
        user.otp_created_at = otp_created_at
        user.save(update_fields=["otp_hash", "otp_created_at"])
        
        return Response({"message": "OTP resent to your email."}, status=200)


class ApprovedUserTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            
            email = request.data.get('username') or request.data.get('email')
            user = User.objects.get(email=email)

            if user.is_superuser:
            
                response = super().post(request, *args, **kwargs)
                return response
            
            
            if user.account_locked_until and user.account_locked_until > timezone.now():
                wait_minutes = int((user.account_locked_until - timezone.now()).total_seconds() / 60)
                return Response({
                    "error": f"Account is temporarily locked. Please try again in {wait_minutes} minutes."
                }, status=403)
            
            
            if not user.is_fully_active() or not user.is_active:
                if user.user_type == 'normal_customer':
                    return Response({
                        "error": "Please verify your email first."
                    }, status=403)
                else:
                    return Response({
                        "error": "Your account is not yet approved or is inactive."
                    }, status=403)
                
            
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                
                user.reset_login_attempts()
                return response
            else:
                
                user.increment_login_attempts()
                return Response({
                    "error": "Invalid credentials."
                }, status=401)
                
        except User.DoesNotExist:
            return Response({
                "error": "User not found"
            }, status=404)
        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
            print("LOGIN ERROR:\n", traceback_str)
            return Response({
                "error": str(e)
            }, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
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


class AdminDashboardRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
        
        
        pending_users = User.objects.filter(
            is_verified=True,
            is_approved=False,
            is_rejected=False,
            user_type__in=['vendor', 'vip_customer']
        )

        users_data = []
        for user in pending_users:
            users_data.append({
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'user_type': user.user_type,
                'created_at': user.date_joined,
            })
        return Response(users_data, status=200)
  
    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
            
        serializer = AdminDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['id']
        action = serializer.validated_data['action']
        rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
            
        if user.is_approved or user.is_rejected:
            return Response({"error": "User already processed"}, status=400)
            
        if action == 'approve':
            user.is_approved = True
            user.approved_at = timezone.now()
            user.is_active = True
            user.processed_by = request.user
            user.processed_at = timezone.now()
            user.save(update_fields=['is_approved', 'approved_at', 'is_active', 'processed_by', 'processed_at'])
            
            
            send_password_setup_email(
                to_email=user.email,
                set_password_url=f"http://localhost:8000/set-password/{user.id}/"
            )
        elif action == 'reject':
            user.is_rejected = True
            user.rejected_at = timezone.now()
            user.rejection_reason = rejection_reason
            user.processed_by = request.user
            user.processed_at = timezone.now()
            user.save(update_fields=['is_rejected', 'rejected_at', 'rejection_reason', 'processed_by', 'processed_at'])
        
        return Response({
            "message": f"User has been {action}d successfully"
        }, status=200)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        full_name = serializer.validated_data['full_name']
        user_type = serializer.validated_data.get('user_type', 'normal_customer')
        
        
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already in use."}, status=400)

    
        user = User.objects.create_user(
            email=email,
            full_name=full_name,
            user_type=user_type
        )

        
        if user_type == 'normal_customer':
            user.is_approved = True
            user.is_active = True
        else:
            user.is_approved = False
            user.is_active = False
            
        user.save(update_fields=['is_approved', 'is_active'])

        
        otp_hash, otp_created_at = generate_and_send_otp(email)
        user.otp_hash = otp_hash
        user.otp_created_at = otp_created_at
        user.save(update_fields=["otp_hash", "otp_created_at"])

        return Response({"message": "OTP sent to your email."}, status=201)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [OTPVerifyRateThrottle]
   
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or user not found."}, status=404)

        if not user.otp_hash or not user.otp_created_at:
            return Response({"error": "No OTP set for this user."}, status=400)

        if not verify_otp(otp_input, user.otp_hash, user.otp_created_at):
            return Response({"error": "Invalid or expired OTP."}, status=400)

        user.is_verified = True
        user.otp_hash = None
        user.save(update_fields=["is_verified", "otp_hash"])

        message = "OTP verified successfully."
        if user.user_type == 'normal_customer':
            message += f" You can now set your password at: /set-password/{user.id}/"
        else:
            message += " Please wait for admin approval."
            
        return Response({"message": message}, status=200)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ResendOTPThrottle]
   
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        otp_hash, otp_created_at = generate_and_send_otp(email)
        user.otp_hash = otp_hash
        user.otp_created_at = otp_created_at
        user.save(update_fields=["otp_hash", "otp_created_at"])

        return Response({"message": "Password reset OTP sent to your email."}, status=200)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    # throttle_classes = [OTPVerifyRateThrottle]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_input = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        if not user.otp_hash or not user.otp_created_at:
            return Response({"error": "No OTP set for this user."}, status=400)

        if not verify_otp(otp_input, user.otp_hash, user.otp_created_at):
            return Response({"error": "Invalid or expired OTP."}, status=400)

        user.password = make_password(new_password)
        user.otp_hash = None
        user.otp_created_at = None
        user.save(update_fields=["password", "otp_hash", "otp_created_at"])

        return Response({"message": "Password reset successfully. You can now log in with your new password."}, status=200)


class SetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id):
        serializer = PasswordSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        if user.is_rejected:
            return Response({"error": "User account has been rejected."}, status=403)
            
        if user.user_type == 'normal_customer':
            if not user.is_verified:
                return Response({"error": "Please verify your email first."}, status=403)
        else:
            if not user.is_active or not user.is_approved:
                return Response({"error": "User is not approved/active."}, status=403)
            
        if user.has_usable_password():
            return Response({"error": "Password has already been set for this account."}, status=400)

        user.password = make_password(password)
        user.save(update_fields=["password"])
        
        return Response({"message": "Password set successfully. You can now log in."}, status=200)
