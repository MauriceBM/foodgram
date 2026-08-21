from django.contrib import admin

from interactions.models import Favorite, ShoppingCart


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель избранного."""

    list_display = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель корзины."""

    list_display = ('user', 'recipe')
