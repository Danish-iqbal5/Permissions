from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView , Response
from rest_framework.permissions import IsAdminUser ,IsAuthenticated , AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from .models import User
from django.contrib.auth.hashers import make_password, check_password
from .utils import send_otp_email , send_password_setup_email
from django.utils import timezone
from .serializers import UserSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        UserALreadyExists = False
        username = request.data.get('username')
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            UserALreadyExists = False
            return Response({"error": "Email already in use."}, status=400)
        if User.objects.filter(username=username).exists():
            UserALreadyExists = False
            return Response({"error": "Username already in use."}, status=400)

        if not UserALreadyExists:
           
            user = User.objects.create(
                username=username,
                email=email,
                otp=send_otp_email(email)
            )


        return Response({"otp Send to your mail  .. Successfully"}, status=201)



class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"Invalid email"}, status=400)

        if user.otp != otp:
            return Response({"Invalid OTP."}, status=400)


        if timezone.now() > user.created_at + timedelta(minutes=10):
            return Response({"error": "OTP has expired."}, status=400)

        user.is_verified = True
        user.save()

        return Response({"message": "OTP verified successfully."}, status=200)
    

class AdminDashboardRequestApprovalView(APIView):
    def get(self, request):
        data = User.objects.all()
        serializer = UserSerializer(data, many=True)
        # serializer = AdminDashboardRequestApprovalSerializer(requests, many=True)
        return Response(serializer.data)

    def post(self, request):
        pending_user_id = request.data.get('pending_user_id')

        try:
            pending_user = User.objects.get(id=pending_user_id, is_verified=True)
        except User.DoesNotExist:
            return Response({"error": "Pending user not found or not verified."}, status=404)

        if User.objects.filter(pending_user=pending_user).exists():
            return Response({"error": "Request already submitted."}, status=400)

        User.objects.create(pending_user=pending_user)

        return Response({"message": "Request submitted for admin approval."}, status=201)
    def patch(self, request):
        pk = request.data.get('id')
        

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({"error": "Approval request not found."}, status=404)
        
        
        if not user.is_verified:
            return Response({"error": "User is not verified."}, status=400)
        
        if not user.is_active:
            user.is_active = True
            user.approved_at = timezone.now()
            user.save()
            mail_sent =  send_password_setup_email(user.email, f"http://localhost:8000/set-password/{user.id}/")
            if mail_sent:
                print("Mail sent successfully")

        
            

        return Response({"message": "Request updated successfully."}, status=200)
    


class SetPasswordView(APIView):
    def post(self, request, user_id):
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required."}, status=400)

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "Invalid or inactive user."}, status=404)

        user.password = make_password(password)
        user.save()
        return Response({"message": "Password set successfully."}, status=200)    