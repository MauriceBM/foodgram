from http import HTTPStatus

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from interactions.models import Favorite, ShoppingCart
from interactions.serializers import (
    FavoriteSerializer,
    ShoppingCartSerializer,
)


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для избранного."""

    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'delete']
    queryset = Favorite.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('pk')
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        deleted_count, _ = Favorite.objects.filter(
            user=request.user,
            recipe_id=self.kwargs.get('pk'),
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не в избранном.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(status=HTTPStatus.NO_CONTENT)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для корзины."""

    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'delete']
    queryset = ShoppingCart.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('pk')
        return context

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe_id=self.kwargs.get('pk'),
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не в корзине.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(status=HTTPStatus.NO_CONTENT)
