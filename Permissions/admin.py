from django.contrib import admin
from .models import User, PendingUser, AdminDashboardRequestApproval, UserProfile

# Register your models here.
admin.site.register(User)
admin.site.register(PendingUser)
admin.site.register(AdminDashboardRequestApproval)
admin.site.register(UserProfile)