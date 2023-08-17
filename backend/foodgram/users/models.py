from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username = models.CharField(
        "nickname",
        max_length=144,
        unique=True,
    )
    first_name = models.CharField("имя", max_length=144)
    last_name = models.CharField("фамилия", max_length=144)
    email = models.EmailField("почта", unique=True, max_length=144)

    class Meta:
        ordering = ["id"]
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписчиков."""

    user = models.ForeignKey(
        User,
        related_name="subscriber",
        verbose_name="подписчик",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name="subscribing",
        verbose_name="автор",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ["-id"]
        constraints = [
            UniqueConstraint(fields=["user", "author"], name="unique_subscription")
        ]
        verbose_name = "подписка"
        verbose_name_plural = "подписки"

    def __str__(self):
        return self.user
