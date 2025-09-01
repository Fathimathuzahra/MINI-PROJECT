from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from django.contrib.auth import get_user_model  # ✅ Correct
User = get_user_model()

from .models import MenuItem

admin.site.register(MenuItem)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'phone', 'role', 'is_staff']  # make sure 'phone' and 'role' exist in model
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone', 'role')}),
    )

