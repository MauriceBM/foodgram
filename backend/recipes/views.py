from http import HTTPStatus
from io import BytesIO

from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from interactions.permissions import IsAuthorOrReadOnly
from recipes.filters import RecipeFilter
from recipes.models import Ingredient, Recipe, Tag
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

    queryset = Recipe.objects.select_related(
        'author'
    ).prefetch_related('tags', 'recipe_ingredients')
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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

    def perform_update(self, serializer):
        serializer.save()

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_relation(
            request, recipe, 'favorite',
            'Рецепт уже в избранном.',
        )

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._toggle_relation(
            request, recipe, 'shopping_cart',
            'Рецепт уже в корзине.',
        )

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        buffer = self._generate_shopping_cart(request.user)
        response = FileResponse(
            buffer, content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response

    def _toggle_relation(
        self, request, recipe, relation_name, error_msg
    ):
        from interactions.models import (
            Favorite,
            ShoppingCart,
        )

        model_map = {
            'favorite': Favorite,
            'shopping_cart': ShoppingCart,
        }
        model = model_map[relation_name]

        if request.method == 'POST':
            if model.objects.filter(
                user=request.user, recipe=recipe
            ).exists():
                return Response(
                    {'errors': error_msg},
                    status=HTTPStatus.BAD_REQUEST,
                )
            model.objects.create(
                user=request.user, recipe=recipe
            )
            serializer = RecipeReadSerializer(
                recipe, context={'request': request}
            )
            return Response(
                serializer.data, status=HTTPStatus.CREATED
            )

        obj = model.objects.filter(
            user=request.user, recipe=recipe
        ).first()
        if obj:
            obj.delete()
        return Response(status=HTTPStatus.NO_CONTENT)

    @staticmethod
    def _generate_shopping_cart(user):
        from interactions.models import ShoppingCart

        cart_items = ShoppingCart.objects.filter(
            user=user
        ).select_related('recipe').prefetch_related(
            'recipe__recipe_ingredients__ingredient'
        )
        ingredients_dict = {}
        for item in cart_items:
            for ri in item.recipe.recipe_ingredients.all():
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                amount = ri.amount
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

        buffer = BytesIO('\n'.join(lines).encode('utf-8'))
        buffer.seek(0)
        return buffer
