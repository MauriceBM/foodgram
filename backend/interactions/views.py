from http import HTTPStatus

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from interactions.models import Favorite, ShoppingCart
from interactions.serializers import (
    FavoriteSerializer,
    ShoppingCartSerializer,
)
from recipes.models import Recipe


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для избранного."""

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            Recipe, id=kwargs.get('pk')
        )
        serializer = self.get_serializer(data={
            'user': request.user.id,
            'recipe': recipe.id,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data, status=HTTPStatus.CREATED
        )

    def destroy(self, request, *args, **kwargs):
        favorite = get_object_or_404(
            Favorite,
            user=request.user,
            recipe_id=kwargs.get('pk'),
        )
        favorite.delete()
        return Response(status=HTTPStatus.NO_CONTENT)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для корзины."""

    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            Recipe, id=kwargs.get('pk')
        )
        serializer = self.get_serializer(data={
            'user': request.user.id,
            'recipe': recipe.id,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data, status=HTTPStatus.CREATED
        )

    def destroy(self, request, *args, **kwargs):
        cart_item = get_object_or_404(
            ShoppingCart,
            user=request.user,
            recipe_id=kwargs.get('pk'),
        )
        cart_item.delete()
        return Response(status=HTTPStatus.NO_CONTENT)
