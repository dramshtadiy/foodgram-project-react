from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField("Название", max_length=144)
    measurement_unit = models.CharField("Единица измерения", max_length=144)

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField("Название", unique=True, max_length=144)
    color = models.CharField(
        "Палитра цвета в формате HEX",
        unique=True,
        max_length=7,
        validators=[RegexValidator(regex="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")],
    )
    slug = models.SlugField("слаг", unique=True, max_length=144)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField("Название", max_length=144)
    author = models.ForeignKey(
        User,
        related_name="recipes",
        on_delete=models.CASCADE,
        null=True,
        verbose_name="автор",
    )
    text = models.TextField("Описание")
    image = models.ImageField("Изображение", upload_to="recipes/img/")
    cooking_time = models.PositiveIntegerField(
        "Время приготовления",
        validators=[
            MinValueValidator(1, "Время приготовления не должно быть меньше 1 минуты")
        ],
    )

    tags = models.ManyToManyField(Tag, related_name="recipes", verbose_name="Теги")

    class Meta:
        ordering = [
            "id",
        ]
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель состава рецепта."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="RecipeIngredient",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[
            MinValueValidator(1, "Время приготовления не должно быть меньше 1 минуты")
        ],
    )

    class Meta:
        verbose_name = "ингредиент в рецепте"
        verbose_name_plural = "ингредиенты в рецептах"

    def __str__(self):
        return self.recipe.name


class Favourites(models.Model):
    """Модель избранного пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранное"
        constraints = [
            UniqueConstraint(fields=["user", "recipe"], name="unique_favourite")
        ]

    def __str__(self):
        return f"{self.user} добавил в избранное {self.recipe} "


class Carts(models.Model):
    """Модель корзины."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        constraints = [UniqueConstraint(fields=["user", "recipe"], name="unique_carts")]

    def __str__(self):
        return f"{self.user} добавил в козину {self.recipe} "
