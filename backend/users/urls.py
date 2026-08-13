from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from interactions.views import SubscriptionViewSet

subscription_list = SubscriptionViewSet.as_view({
    'get': 'subscriptions_list',
})
subscription_detail = SubscriptionViewSet.as_view({
    'post': 'subscribe',
    'delete': 'unsubscribe',
})

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path(
        'users/subscriptions/',
        subscription_list,
        name='subscriptions-list',
    ),
    path(
        'users/<int:pk>/subscribe/',
        subscription_detail,
        name='user-subscribe',
    ),
    path('', include(router.urls)),
    path(
        'auth/',
        include('djoser.urls.authtoken'),
    ),
]
