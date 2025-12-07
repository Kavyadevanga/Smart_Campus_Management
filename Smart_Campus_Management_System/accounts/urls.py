from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoginAPIView, DepartmentViewSet

# Create DRF router and register UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'departments', DepartmentViewSet, basename='departments')

# Combine router URLs with other paths
urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('', include(router.urls)),  # include all router-generated URLs
]
