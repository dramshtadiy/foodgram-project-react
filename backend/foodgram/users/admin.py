from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribe, User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Регистрация модели пользователя в админ-панели."""

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    list_filter = ("email", "first_name")
    search_fields = ("username",)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Регистрация подписчиков в админ-панели."""

    list_display = (
        "user",
        "author",
    )
    list_filter = ("user", "author")
    search_fields = ("username",)
