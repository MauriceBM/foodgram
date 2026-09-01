from rest_framework import serializers

from interactions.models import Favorite, ShoppingCart


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def create(self, validated_data):
        recipe_id = self.context.get('recipe_id')
        validated_data['recipe_id'] = recipe_id
        return super().create(validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор корзины."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def create(self, validated_data):
        recipe_id = self.context.get('recipe_id')
        validated_data['recipe_id'] = recipe_id
        return super().create(validated_data)
