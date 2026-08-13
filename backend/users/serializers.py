import base64
from django.core.files.base import ContentFile
from djoser.serializers import (
    UserCreateSerializer,
    UserSerializer,
)
from rest_framework import serializers
from .models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Serializer for user registration."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    """Serializer for user profile."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if (
            request is None
            or not request.user.is_authenticated
        ):
            return False
        return obj.subscribers.filter(
            user=request.user
        ).exists()


class Base64ImageField(serializers.ImageField):
    """Custom field to decode base64 images."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            if ';base64,' in data:
                header, encoded = data.split(
                    ';base64,', 1
                )
                ext = header.split('/')[-1]
                decoded = base64.b64decode(encoded)
                data = ContentFile(
                    decoded,
                    name=f'avatar.{ext}'
                )
        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for avatar upload/delete."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for password change."""

    new_password = serializers.CharField(
        required=True
    )
    current_password = serializers.CharField(
        required=True
    )
