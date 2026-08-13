from rest_framework import serializers
from recipes.serializers import RecipeReadSerializer


class FavoriteRecipeSerializer(serializers.Serializer):
    """Minimal recipe serializer for favorites/cart."""

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    image = serializers.ImageField(read_only=True)
    cooking_time = serializers.IntegerField(
        read_only=True
    )


class SubscriptionSerializer(serializers.Serializer):
    """Serializer for subscription response."""

    email = serializers.EmailField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_subscribed = serializers.BooleanField(
        read_only=True
    )
    recipes = RecipeReadSerializer(
        many=True,
        read_only=True,
    )
    recipes_count = serializers.IntegerField(
        read_only=True
    )
    avatar = serializers.ImageField(read_only=True)
