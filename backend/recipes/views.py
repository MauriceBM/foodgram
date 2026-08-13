from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from .models import Tag, Ingredient, Recipe
from .serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Tags are read-only via API."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Ingredients with search by name."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(
                name__istartswith=name
            )
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Full CRUD for recipes + custom actions."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        queryset = Recipe.objects.select_related(
            'author'
        ).prefetch_related(
            'tags', 'recipe_ingredients__ingredient'
        )
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(
                tags__slug__in=tags
            ).distinct()

        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)

        is_favorited = self.request.query_params.get(
            'is_favorited'
        )
        if is_favorited == '1':
            user = self.request.user
            if user.is_authenticated:
                queryset = queryset.filter(
                    favorites__user=user
                )

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart == '1':
            user = self.request.user
            if user.is_authenticated:
                queryset = queryset.filter(
                    shopping_cart_entries__user=user
                )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        read_serializer = RecipeReadSerializer(
            recipe,
            context={'request': request},
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeReadSerializer(
            instance,
            context={'request': request},
        )
        return Response(read_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeReadSerializer(
            instance,
            context={'request': request},
        )
        return Response(read_serializer.data)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = f'{request.scheme}://'
        short_link += f'{request.get_host()}/s/'
        short_link += f'{recipe.id}'
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        from interactions.models import Favorite
        recipe = self.get_object()
        if request.method == 'POST':
            obj, created = Favorite.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'detail': 'Already in favorites.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': recipe.image.url,
                    'cooking_time': recipe.cooking_time,
                },
                status=status.HTTP_201_CREATED,
            )
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Not in favorites.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping-cart',
    )
    def shopping_cart(self, request, pk=None):
        from interactions.models import ShoppingCart
        recipe = self.get_object()
        if request.method == 'POST':
            obj, created = ShoppingCart.objects.get_or_create(
                user=request.user,
                recipe=recipe,
            )
            if not created:
                return Response(
                    {'detail': 'Already in shopping cart.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    'id': recipe.id,
                    'name': recipe.name,
                    'image': recipe.image.url,
                    'cooking_time': recipe.cooking_time,
                },
                status=status.HTTP_201_CREATED,
            )
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Not in shopping cart.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download-shopping-cart',
    )
    def download_shopping_cart(self, request):
        from interactions.models import ShoppingCart

        items = (
            ShoppingCart.objects.filter(user=request.user)
            .values(
                'recipe__recipe_ingredients__ingredient__name',
                'recipe__recipe_ingredients__ingredient__measurement_unit',
            )
            .annotate(
                total=Sum(
                    'recipe__recipe_ingredients__amount'
                )
            )
        )
        lines = []
        for item in items:
            name = item[
                'recipe__recipe_ingredients__ingredient__name'
            ]
            unit = item[
                'recipe__recipe_ingredients__ingredient__measurement_unit'
            ]
            total = item['total']
            lines.append(f'{name} ({unit}) — {total}')

        content = '\n'.join(lines)
        response = Response(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
