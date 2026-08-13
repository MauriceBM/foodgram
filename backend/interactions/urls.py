from .views import SubscriptionViewSet

subscription_list = SubscriptionViewSet.as_view({
    'get': 'subscriptions_list',
})
subscription_detail = SubscriptionViewSet.as_view({
    'post': 'subscribe',
    'delete': 'unsubscribe',
})

urlpatterns = []
