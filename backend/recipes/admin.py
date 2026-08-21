from django.contrib import admin

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для ингредиентов рецепта."""

    model = RecipeIngredient
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель рецептов."""

    list_display = (
        'name', 'author', 'cooking_time', 'pub_date',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('tags', 'pub_date')
    inlines = (RecipeIngredientInline,)
