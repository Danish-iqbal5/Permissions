from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView , Response
from rest_framework.permissions import IsAdminUser ,IsAuthenticated , AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from .models import PendingUser , UserProfile , AdminDashboardRequestApproval
from django.contrib.auth.hashers import make_password, check_password
from .utils import send_otp_email
from django.utils import timezone

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        UserALreadyExists = False
        username = request.data.get('username')
        email = request.data.get('email')
        if PendingUser.objects.filter(email=email).exists() or UserProfile.objects.filter(user__email=email).exists():
            UserALreadyExists = False
            return Response({"error": "Email already in use."}, status=400)
        if PendingUser.objects.filter(username=username).exists() or UserProfile.objects.filter(user__username=username).exists():
            UserALreadyExists = False
            return Response({"error": "Username already in use."}, status=400)

        if not UserALreadyExists:
           
            pending_user = PendingUser.objects.create(
                username=username,
                email=email,
                otp=send_otp_email(email)
            )


        return Response({"Registeration Request Send To Admin .. Successfully"}, status=201)