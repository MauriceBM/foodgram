from http import HTTPStatus

from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Subscription
from recipes.serializers import SubscriptionSerializer
from users.models import User
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False, methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=HTTPStatus.OK)

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
                serializer.data, status=HTTPStatus.CREATED,
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
            page, many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer.data)
