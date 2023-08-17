import djoser.serializers
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from recipes.models import (Carts, Favourites, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer
from users.models import Subscribe, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для создания Юзера."""

    class Meta:
        model = User
        fields = ("id",
                  "username",
                  "first_name",
                  "last_name",
                  "email",
                  "password")
        extra_kwargs = {"password": {"write_only": True}}

    @staticmethod
    def validate_(data):
        """Проверка на дублирование username и email."""
        if User.objects.filter(username=data.get("username")):
            raise serializers.ValidationError(
                "Пользователь с данным username уже существует."
            )
        if User.objects.filter(email=data.get("email")):
            raise serializers.ValidationError(
                "Данный email занят другим пользователем."
            )
        return data


class CustomUserSerializer(UserSerializer):
    """Сериализатор модели пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("email",
                  "id",
                  "username",
                  "first_name",
                  "last_name",
                  "is_subscribed")

    def get_is_subscribed(self, obj):
        """Флаг на подписку пользователя."""
        user = self.context.get("request").user
        if user.is_anonymous or (user == obj):
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class SubscribeSerializer(djoser.serializers.UserSerializer):
    """Сериализатор получение списка подписок."""

    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("email", "username", "first_name", "last_name")

    def validate(self, data):
        """Валидация подписки на пользователя. """
        author = get_object_or_404(User, id=id)
        user = self.context.get("request").user
        if user == author:
            raise ValidationError(
                detail="Нельзя подписаться на самого себя",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data

    @staticmethod
    def get_recipes(obj):
        """Получение рецептов у подписки."""
        author = obj.recipes.all()
        return RecipeSubscribedSerializer(author, many=True).data

    @staticmethod
    def get_recipes_count(obj):
        """Получения кол-ва рецептов у подписки."""
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        """Флаг на подписку пользователя."""
        user = self.context.get("request").user
        if user.is_anonymous or (user == obj):
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class RecipeSubscribedSerializer(ModelSerializer):
    """Сериализатор для получения рецепта в страницу подписок."""

    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image",
            "cooking_time",
        ]


class IngredientSerializer(ModelSerializer):
    """Сериализатор Ингридиентов. """

    class Meta:
        model = Ingredient
        fields = "__all__"


class IngredientRecipeSerializer(ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    name = SerializerMethodField()
    measurement_unit = SerializerMethodField()
    id = SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = [
            "id",
            "name",
            "amount",
            "measurement_unit",
        ]

    @staticmethod
    def get_id(obj):
        """Получение id ингредиента."""
        return obj.ingredient.id

    @staticmethod
    def get_name(obj):
        """Получение название ингредиента."""
        return obj.ingredient.name

    @staticmethod
    def get_measurement_unit(obj):
        """Получение единиц измерения ингредиента."""
        return obj.ingredient.measurement_unit


class TagSerializer(ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = "__all__"


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор чтения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    @staticmethod
    def get_ingredients(obj):
        """Получение ингредиентов к рецепту."""
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        """Возвращает флаг о нахождении рецепта в избранном."""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Favourites.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Возвращает флаг о нахождении рецепта в корзине."""
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Carts.objects.filter(user=user, recipe=obj).exists()


class IngredientInRecipeWriteSerializer(ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeWriteSerializer(ModelSerializer):
    """Сериализатор добавление и редактирования рецепта."""

    tags = PrimaryKeyRelatedField(
        queryset=Tag.objects.all().values_list("id", "name"), many=True
    )
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "name",
            "image",
            "text",
            "cooking_time",
            "author",
        )

    @staticmethod
    def validate_ingredients(value):
        ingredients = value
        if not ingredients:
            raise ValidationError(
                {"ingredients": "Нужен хотя бы один ингредиент!"}
            )
        ingredients_list = []
        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item["id"])
            if ingredient in ingredients_list:
                raise ValidationError(
                    {"ingredients": "Ингридиенты не могут повторяться!"}
                )
            if int(item["amount"]) <= 0:
                raise ValidationError(
                    {"amount": "Количество ингредиента должно быть больше 0!"}
                )
            ingredients_list.append(ingredient)
        return value

    @transaction.atomic
    def create_ingredients_amounts(self, ingredients, recipe):
        """Добавление ингредиентов к созданному рецепту."""
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    ingredient=Ingredient.objects.get(id=ingredient["id"]),
                    recipe=recipe,
                    amount=ingredient["amount"],
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create_tags(self, recipe, tags):
        """Добавление тэгов к созданному рецепту."""
        for tag in tags:
            recipe.tags.add(int(tag[0]))

    @transaction.atomic
    def create(self, validated_data):
        """Добавление рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.create_tags(recipe=recipe, tags=tags)
        self.create_ingredients_amounts(recipe=recipe, ingredients=ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Редактирование рецепта."""
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_tags(recipe=instance, tags=tags)
        self.create_ingredients_amounts(recipe=instance,
                                        ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Возвращаемый объект после изменения."""
        request = self.context.get("request")
        context = {"request": request}
        return RecipeReadSerializer(instance, context=context).data


class RecipeShortSerializer(ModelSerializer):
    """Сериализатор рецепта. """

    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
