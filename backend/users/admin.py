from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Админ-панель пользователя."""

    list_display = (
        'email', 'username', 'first_name',
        'last_name', 'is_staff',
    )
    search_fields = (
        'email', 'username', 'first_name', 'last_name',
    )
    list_filter = ('is_staff', 'is_active')
    ordering = ('email',)
