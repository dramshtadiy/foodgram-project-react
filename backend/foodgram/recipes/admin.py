from django.contrib import admin
from django.contrib.admin import display

from .models import Favourites, Ingredient, RecipeIngredient, Recipe, Carts, Tag


class IngredientInLine(admin.TabularInline):
    """
    Инлайн для добавления ингредиентов при создании рецепта через админ-панель.
    """

    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Регистрация модели рецептов в админ-панели."""

    inlines = (IngredientInLine,)
    list_display = (
        "name",
        "id",
        "author",
        "added_in_favorites"
    )
    readonly_fields = (
        "added_in_favorites",
    )
    list_filter = (
        "author",
        "name",
        "tags"
    )

    @display(description="Количество в избранных")
    def added_in_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Регистрация ингредиентов в админ-панели."""

    list_display = (
        "name",
        "measurement_unit"
    )
    list_filter = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Регистрация тегов в админ-панели."""

    list_display = (
        "name",
        "color",
        "slug"
    )


@admin.register(Carts)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Регистрация модели корзины в админ-панели."""

    list_display = (
        "user",
        "recipe"
    )


@admin.register(Favourites)
class FavouriteAdmin(admin.ModelAdmin):
    """Регистрация модели избранное в админ-панели."""

    list_display = (
        "user",
        "recipe"
    )
