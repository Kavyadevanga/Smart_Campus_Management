from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, EventParticipantsViewSet

# Create DRF router and register ViewSets
router = DefaultRouter()
router.register(r'events', EventViewSet, basename='events')
router.register(r'participants', EventParticipantsViewSet, basename='event-participants')

urlpatterns = [
    path('', include(router.urls)),
]
