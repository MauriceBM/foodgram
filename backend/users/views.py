from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    AvatarSerializer,
    SetPasswordSerializer,
)


class UserViewSet(BaseUserViewSet):
    """Custom UserViewSet with avatar and password."""

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
        url_name='avatar',
    )
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        request.user.avatar.delete(save=True)
        return Response(status=204)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
        url_name='set-password',
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': ['Wrong password.']},
                status=400,
            )
        request.user.set_password(
            serializer.validated_data['new_password']
        )
        request.user.save()
        return Response(status=204)
