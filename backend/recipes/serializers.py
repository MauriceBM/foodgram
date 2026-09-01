from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User
from users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.Serializer):
    """Сериализатор ингредиента в рецепте."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор чтения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(
        read_only=True, default=False,
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False,
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_ingredients(self, obj):
        recipe_ingredients = (
            obj.recipe_ingredients.select_related('ingredient')
        )
        return [
            {
                'id': relation.ingredient.id,
                'name': relation.ingredient.name,
                'measurement_unit': (
                    relation.ingredient.measurement_unit
                ),
                'amount': relation.amount,
            }
            for relation in recipe_ingredients
        ]


class RecipeCreateUpdateSerializer(
    serializers.ModelSerializer,
):
    """Сериализатор создания/обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
    )
    ingredients = RecipeIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': (
                    'Нужен хотя бы один ингредиент.'
                ),
            })
        ids = [item['id'] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({
                'ingredients': (
                    'Ингредиенты не должны повторяться.'
                ),
            })
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужен хотя бы один тег.',
            })
        return data

    def _save_tags_and_ingredients(self, recipe, validated_data):
        """Сохранение тегов и ингредиентов рецепта."""
        tags = validated_data.pop('tags')
        recipe.tags.set(tags)
        ingredients_data = validated_data.pop('ingredients')
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(
            recipe_ingredients,
        )

    def create(self, validated_data):
        recipe = Recipe.objects.create(**validated_data)
        self._save_tags_and_ingredients(
            recipe, validated_data,
        )
        return recipe

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self._save_tags_and_ingredients(
            instance, validated_data,
        )
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    email = serializers.EmailField(source='email')
    first_name = serializers.CharField(source='first_name')
    last_name = serializers.CharField(source='last_name')
    username = serializers.CharField(source='username')
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.IntegerField(
        read_only=True, default=0,
    )
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name',
            'username', 'is_subscribed',
            'recipes_count', 'recipes',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        if request:
            limit = request.query_params.get(
                'recipes_limit',
            )
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeReadSerializer(
            recipes, many=True, context=self.context,
        ).data
