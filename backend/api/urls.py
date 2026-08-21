from django.urls import include, path
from rest_framework.routers import DefaultRouter

from interactions.views import (
    FavoriteViewSet,
    ShoppingCartViewSet,
)
from recipes.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
)
from users.views import CustomUserViewSet

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register(
    'ingredients', IngredientViewSet, basename='ingredients'
)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/<int:pk>/favorite/',
        FavoriteViewSet.as_view({
            'post': 'create', 'delete': 'destroy'
        }),
        name='recipe-favorite',
    ),
    path(
        'recipes/<int:pk>/shopping_cart/',
        ShoppingCartViewSet.as_view({
            'post': 'create', 'delete': 'destroy'
        }),
        name='recipe-shopping-cart',
    ),
]
