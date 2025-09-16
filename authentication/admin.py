from django.contrib import admin
# from .models import UserProfile
from django.contrib.auth.models import User
from .models import User

admin.site.register(User)


# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
# 	list_display = ("user", "full_name", "is_verified", "is_approved", "is_rejected", "approved_at", "rejected_at")
# 	list_filter = ("is_verified", "is_approved", "is_rejected")
# 	search_fields = ("user__username", "user__email", "full_name", "phone_number")