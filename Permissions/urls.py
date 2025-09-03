from django.urls import path
from . import views

urlpatterns = [
    path('set-password/<uuid:user_id>/', views.SetPasswordView.as_view(), name='set-password'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('admin-dashboard/', views.AdminDashboardRequestApprovalView.as_view(), name='admin-requests'),
]
