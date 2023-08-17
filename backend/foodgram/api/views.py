import io

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Carts, Favourites, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import exceptions, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import Subscribe, User

from .filters import RecipeFilter
from .paginations import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SubscribeSerializer,
                          TagSerializer)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет ингредиента."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = [DjangoFilterBackend]
    pagination_class = None


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = PageLimitPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def add_to(model, user, pk):
        """Добавление рецепта в избранное или в список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        """Получение сериализатора в зависимости от метода."""
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=[
            "post",
            "delete",
        ],
        url_path="favorite",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def favorite(self, request, pk):
        """Добавление и удаление рецепта из избранного."""
        if request.method == "POST":
            return self.add_to(model=Favourites, user=request.user, pk=pk)
        else:
            Favourites.objects.filter(user=request.user, recipe_id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        url_path="shopping_cart",
        methods=[
            "post",
            "delete",
        ],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def shopping_cart(self, request, pk):
        """Добавление и удаление рецепта из списка покупок."""
        if request.method == "POST":
            return self.add_to(model=Carts, user=request.user, pk=pk)
        else:
            Carts.objects.filter(recipe_id=pk, user=request.user).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path="download_shopping_cart",
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def download_carts(self, request):
        """Формирование и загрузка текстового файла с ингредиентами."""
        carts = (
            Carts.objects.select_related("recipe")
            .filter(user=request.user)
            .values_list("recipe_id", flat=True)
        )
        output = io.StringIO()
        data = {}
        for recipe in carts:
            ingredients = RecipeIngredient.objects.values_list(
                "ingredient__name", "ingredient__measurement_unit", "amount"
            ).filter(recipe_id=recipe)
            for item in ingredients:
                if item[0] in data:
                    data[item[0]]["amount"] += int(item[2])
                else:
                    data[item[0]] = {
                        "amount": int(item[2]), "unit": item[1]}
        for key in data.keys():
            output.write(
                f'{key} - {data[key]["amount"]} {data[key]["unit"]}\n'
            )
        filename = "carts.txt"
        response = FileResponse(output.getvalue(), content_type="text.txt")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response


class CustomUserViewSet(UserViewSet):
    """Вьюсет для работы с пользователем."""

    queryset = User.objects.all()
    pagination_class = PageLimitPagination
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthorOrReadOnly,)

    @staticmethod
    def get_user(id_user):
        """Получение объекта пользователя."""
        return get_object_or_404(User, id=id_user)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=(IsAuthorOrReadOnly,),
    )
    def get_subscriptions(self, request):
        """Получение подписок."""
        queryset = User.objects.filter(subscribing__user=request.user.pk)
        pages = self.paginate_queryset(queryset=queryset)
        serializer = SubscribeSerializer(pages,
                                         many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=SubscribeSerializer,
    )
    def subscribe(self, request, **kwargs):
        """Подписка на пользователя."""
        author = self.get_user(id_user=kwargs["id"])
        if request.user == author:
            raise exceptions.ValidationError(
                "Невозможно подписаться на себя ."
                )
        _, created = Subscribe.objects.get_or_create(
            user=request.user,
            author=author)
        if not created:
            raise exceptions.ValidationError(f"Вы уже подписаны на {author}")
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Отписка от пользователя."""
        author = self.get_user(id_user=kwargs["id"])
        get_object_or_404(Subscribe, user=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
