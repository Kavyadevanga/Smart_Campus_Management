from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoginAPIView, DepartmentViewSet, GroupViewSet, PermissionListView

# Create DRF router and register ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'groups', GroupViewSet, basename='groups')

# Combine router URLs with other paths
urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('permissions/', PermissionListView.as_view(), name='permissions-list'),
    path('', include(router.urls)),  # include all router-generated URLs
]
