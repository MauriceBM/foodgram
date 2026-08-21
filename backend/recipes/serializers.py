from rest_framework import serializers

from recipes.models import Ingredient, Recipe, Tag
from users.models import CustomUser


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
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_author(self, obj):
        from users.serializers import CustomUserSerializer
        return CustomUserSerializer(
            obj.author, context=self.context
        ).data

    def get_ingredients(self, obj):
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': (
                    ri.ingredient.measurement_unit
                ),
                'amount': ri.amount,
            }
            for ri in (
                obj.recipe_ingredients
                .select_related('ingredient')
            )
        ]

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.favorites.filter(
            user=request.user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.shopping_carts.filter(
            user=request.user
        ).exists()


class RecipeCreateUpdateSerializer(
    serializers.ModelSerializer
):
    """Сериализатор создания/обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
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
                )
            })
        ids = [i['id'] for i in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError({
                'ingredients': (
                    'Ингредиенты не должны повторяться.'
                )
            })
        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужен хотя бы один тег.'
            })
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for item in ingredients_data:
            ingredient = Ingredient.objects.get(id=item['id'])
            Recipe.objects.get(
                id=recipe.id
            ).recipe_ingredients.create(
                ingredient=ingredient,
                amount=item['amount'],
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop(
            'ingredients', None
        )
        tags = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for item in ingredients_data:
                ingredient = Ingredient.objects.get(
                    id=item['id']
                )
                instance.recipe_ingredients.create(
                    ingredient=ingredient,
                    amount=item['amount'],
                )
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор подписки."""

    email = serializers.EmailField(source='email')
    first_name = serializers.CharField(source='first_name')
    last_name = serializers.CharField(source='last_name')
    username = serializers.CharField(source='username')
    is_subscribed = serializers.BooleanField(default=True)
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email', 'first_name', 'last_name',
            'username', 'is_subscribed',
            'recipes_count', 'recipes',
        )

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        if request:
            limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeReadSerializer(
            recipes, many=True, context=self.context
        ).data
