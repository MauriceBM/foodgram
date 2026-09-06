from http import HTTPStatus
from io import BytesIO

from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Value,
)
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserAPISerializer,
)
from interactions.models import Favorite, ShoppingCart
from interactions.permissions import IsAuthorOrReadOnly
from recipes.filters import RecipeFilter
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
)
from users.models import User

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.select_related(
            'author',
        ).prefetch_related(
            'tags', 'recipe_ingredients__ingredient',
        )
        request = self.request
        if request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=request.user,
                        recipe=OuterRef('pk'),
                    ),
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=request.user,
                        recipe=OuterRef('pk'),
                    ),
                ),
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(
                    False, output_field=BooleanField(),
                ),
                is_in_shopping_cart=Value(
                    False, output_field=BooleanField(),
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateUpdateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_relation(
            request, recipe, FavoriteSerializer, Favorite,
            'Рецепт уже в избранном.',
            'Рецепт не в избранном.',
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_relation(
            request, recipe, ShoppingCartSerializer,
            ShoppingCart,
            'Рецепт уже в корзине.',
            'Рецепт не в корзине.',
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        buffer = self._generate_shopping_cart(request.user)
        response = FileResponse(
            buffer, content_type='text/plain',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @staticmethod
    def _toggle_relation(
        request, recipe, serializer_class,
        model, exists_error, not_found_error,
    ):
        if request.method == 'POST':
            if model.objects.filter(
                user=request.user, recipe=recipe,
            ).exists():
                return Response(
                    {'errors': exists_error},
                    status=HTTPStatus.BAD_REQUEST,
                )
            serializer = serializer_class(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id,
                },
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe_serializer = RecipeReadSerializer(
                recipe, context={'request': request},
            )
            return Response(
                recipe_serializer.data,
                status=HTTPStatus.CREATED,
            )
        deleted_count, _ = model.objects.filter(
            user=request.user, recipe=recipe,
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': not_found_error},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(status=HTTPStatus.NO_CONTENT)

    @staticmethod
    def _generate_shopping_cart(user):
        cart_ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart_relations__user=user,
            ).select_related('ingredient')
        )
        ingredients_dict = {}
        for relation in cart_ingredients:
            name = relation.ingredient.name
            unit = relation.ingredient.measurement_unit
            amount = relation.amount
            key = f'{name}_{unit}'
            if key in ingredients_dict:
                ingredients_dict[key]['amount'] += amount
            else:
                ingredients_dict[key] = {
                    'name': name,
                    'unit': unit,
                    'amount': amount,
                }
        lines = ['Список покупок:\n']
        for data in ingredients_dict.values():
            line = (
                f"- {data['name']} — "
                f"{data['amount']} {data['unit']}"
            )
            lines.append(line)
        buffer = BytesIO(
            '\n'.join(lines).encode('utf-8'),
        )
        buffer.seek(0)
        return buffer


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    serializer_class = UserAPISerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(
            serializer.data, status=HTTPStatus.OK,
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={
                    'user': request.user.id,
                    'author': author.id,
                },
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=HTTPStatus.CREATED,
            )
        deleted_count, _ = Subscription.objects.filter(
            user=request.user, author=author,
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Подписка не найдена.'},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            followers__user=request.user,
        ).annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page, many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


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
