from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

# Create DRF router and register ViewSet
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]
