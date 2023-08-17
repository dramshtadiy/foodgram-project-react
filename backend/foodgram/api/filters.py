from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтрация по названию ингредиента."""

    name = filters.CharFilter(field_name="name", lookup_expr="startswith")

    class Meta:
        model = Ingredient
        fields = ("name",)


class RecipeFilter(FilterSet):
    """Фильтрация queryset на избранное и добавленное в корзину."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(method="get_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="get_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = (
            "tags",
            "author",
        )

    def get_is_favorited(self, queryset, name, value):
        """Метод для получения избранных рецептов."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        """Метод для получения рецептов в корзине."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(carts__user=user)
        return queryset
