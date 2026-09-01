from http import HTTPStatus
from io import BytesIO

from django.db.models import BooleanField, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from interactions.models import Favorite, ShoppingCart
from interactions.permissions import IsAuthorOrReadOnly
from recipes.filters import RecipeFilter
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from recipes.serializers import (
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    TagSerializer,
)

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
                is_favorited=Coalesce(
                    Value(True),
                    output_field=BooleanField(),
                ),
                is_in_shopping_cart=Coalesce(
                    Value(True),
                    output_field=BooleanField(),
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
            request, recipe, Favorite,
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
            request, recipe, ShoppingCart,
            'Рецепт уже в корзине.',
            'Рецепт не в корзине.',
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        buffer = self._generate_shopping_cart(
            request.user,
        )
        response = FileResponse(
            buffer, content_type='text/plain',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    @staticmethod
    def _toggle_relation(
        request, recipe, model,
        exists_error, not_found_error,
    ):
        if request.method == 'POST':
            if model.objects.filter(
                user=request.user, recipe=recipe,
            ).exists():
                return Response(
                    {'errors': exists_error},
                    status=HTTPStatus.BAD_REQUEST,
                )
            model.objects.create(
                user=request.user, recipe=recipe,
            )
            serializer = RecipeReadSerializer(
                recipe, context={'request': request},
            )
            return Response(
                serializer.data, status=HTTPStatus.CREATED,
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
                recipe__shopping_carts__user=user,
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
