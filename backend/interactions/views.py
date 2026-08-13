from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from recipes.models import Recipe
from recipes.serializers import RecipeReadSerializer
from users.models import User
from .models import Favorite, ShoppingCart, Subscription
from .serializers import (
    FavoriteRecipeSerializer,
)


class FavoriteMixin:
    """Reusable logic for favorite/cart actions."""

    model = None
    error_already = ''
    error_not_exists = ''

    def _add(self, request, pk):
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Recipe not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        obj, created = self.model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )
        if not created:
            return Response(
                {'detail': self.error_already},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = FavoriteRecipeSerializer(recipe)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def _remove(self, request, pk):
        deleted, _ = self.model.objects.filter(
            user=request.user,
            recipe_id=pk,
        ).delete()
        if not deleted:
            return Response(
                {'detail': self.error_not_exists},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(FavoriteMixin, viewsets.GenericViewSet):
    """Add/remove recipes from favorites."""

    permission_classes = [IsAuthenticated]
    model = Favorite
    error_already = 'Recipe already in favorites.'
    error_not_exists = 'Recipe is not in favorites.'

    @action(detail=True, methods=['post'])
    def add(self, request, pk=None):
        return self._add(request, pk)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        return self._remove(request, pk)


class ShoppingCartViewSet(
    FavoriteMixin, viewsets.GenericViewSet
):
    """Add/remove recipes from shopping cart."""

    permission_classes = [IsAuthenticated]
    model = ShoppingCart
    error_already = 'Recipe already in shopping cart.'
    error_not_exists = 'Recipe is not in shopping cart.'

    @action(detail=True, methods=['post'])
    def add(self, request, pk=None):
        return self._add(request, pk)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        return self._remove(request, pk)


class SubscriptionViewSet(viewsets.GenericViewSet):
    """Subscribe/unsubscribe to authors."""

    permission_classes = [IsAuthenticated]

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, pk=None):
        try:
            author = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if author == request.user:
            return Response(
                {'detail': 'Cannot subscribe to yourself.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sub, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            return Response(
                {'detail': 'Already subscribed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipes_limit = int(
            request.query_params.get('recipes_limit', 3)
        )
        recipes = Recipe.objects.filter(
            author=author
        )[:recipes_limit]
        data = {
            'email': author.email,
            'id': author.id,
            'username': author.username,
            'first_name': author.first_name,
            'last_name': author.last_name,
            'is_subscribed': True,
            'recipes': RecipeReadSerializer(
                recipes,
                many=True,
                context={'request': request},
            ).data,
            'recipes_count': author.recipes.count(),
            'avatar': (
                author.avatar.url if author.avatar else None
            ),
        }
        return Response(
            data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['delete'],
        url_path='subscribe',
        url_name='unsubscribe',
    )
    def unsubscribe(self, request, pk=None):
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author_id=pk,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Not subscribed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        url_name='subscriptions-list',
    )
    def subscriptions_list(self, request):
        subs = Subscription.objects.filter(
            user=request.user
        ).select_related('author')

        page = self.paginate_queryset(subs)
        results = []
        items = page if page is not None else subs

        for sub in items:
            author = sub.author
            recipes_limit = int(
                request.query_params.get(
                    'recipes_limit', 3
                )
            )
            recipes = Recipe.objects.filter(
                author=author
            )[:recipes_limit]
            results.append({
                'email': author.email,
                'id': author.id,
                'username': author.username,
                'first_name': author.first_name,
                'last_name': author.last_name,
                'is_subscribed': True,
                'recipes': RecipeReadSerializer(
                    recipes,
                    many=True,
                    context={'request': request},
                ).data,
                'recipes_count': author.recipes.count(),
                'avatar': (
                    author.avatar.url
                    if author.avatar
                    else None
                ),
            })

        if page is not None:
            return self.get_paginated_response(results)
        return Response(results)
