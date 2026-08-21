from rest_framework import serializers

from interactions.models import Favorite, ShoppingCart


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
