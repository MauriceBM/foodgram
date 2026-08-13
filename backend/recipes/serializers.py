from rest_framework import serializers
from .models import Tag, Ingredient
from .models import Recipe, RecipeIngredient


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientWriteSerializer(
    serializers.Serializer
):
    """Serializer for ingredients in recipe creation."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    """Serializer for reading recipes (nested output)."""

    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = (
        serializers.SerializerMethodField()
    )
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_author(self, obj):
        from users.serializers import CustomUserSerializer
        request = self.context.get('request')
        return CustomUserSerializer(
            obj.author,
            context={'request': request}
        ).data

    def get_ingredients(self, obj):
        recipe_ingredients = (
            obj.recipe_ingredients.select_related(
                'ingredient'
            )
        )
        result = []
        for ri in recipe_ingredients:
            result.append({
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': (
                    ri.ingredient.measurement_unit
                ),
                'amount': ri.amount,
            })
        return result

    def _get_user_flag(self, obj, related_name):
        request = self.context.get('request')
        if (
            request is None
            or not request.user.is_authenticated
        ):
            return False
        return getattr(obj, related_name).filter(
            user=request.user
        ).exists()

    def get_is_favorited(self, obj):
        return self._get_user_flag(obj, 'favorites')

    def get_is_in_shopping_cart(self, obj):
        return self._get_user_flag(
            obj, 'shopping_cart_entries'
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating recipes."""

    ingredients = RecipeIngredientWriteSerializer(
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = serializers.CharField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one tag is required.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'At least one ingredient is required.'
            )
        seen_ids = set()
        for item in value:
            ing_id = item['id']
            if ing_id in seen_ids:
                raise serializers.ValidationError(
                    f'Duplicate ingredient id: {ing_id}'
                )
            seen_ids.add(ing_id)
            if not Ingredient.objects.filter(
                id=ing_id
            ).exists():
                raise serializers.ValidationError(
                    f'Ingredient {ing_id} not found.'
                )
        return value

    def _save_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=item['id'],
                amount=item['amount'],
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(
            **validated_data,
        )
        recipe.tags.set(tags)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop(
            'ingredients', None
        )
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self._save_ingredients(
                instance, ingredients_data
            )

        return instance
