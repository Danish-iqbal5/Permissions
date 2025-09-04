# from django.urls import path
# from . import views
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#    openapi.Info(
#       title="Your API",
#       default_version='v1',
#       description="API documentation for your project",
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
# )

# urlpatterns = [
#     path('set-password/<int:user_id>/', views.SetPasswordView.as_view(), name='set-password'),
#     path('register/', views.RegisterView.as_view(), name='register'),
#     path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
#     path('admin-dashboard/', views.AdminDashboardRequestApprovalView.as_view(), name='admin-requests'),
#     path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
# ]

from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
# Auth
path('register/', views.RegisterView.as_view(), name='register'),
path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
path('resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
path('login/', views.ApprovedUserTokenObtainPairView.as_view(), name='token_obtain_pair'),
path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
path('logout/', views.LogoutView.as_view(), name='logout'),


# Admin
path('admin-dashboard/', views.AdminDashboardRequestApprovalView.as_view(), name='admin-requests'),


# Password
path('set-password/<int:user_id>/', views.SetPasswordView.as_view(), name='set-password'),
]