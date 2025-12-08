from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, EnrollmentViewSet, AttendanceViewSet, GradeViewSet

# Create DRF router and register ViewSets
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'grades', GradeViewSet, basename='grades')

urlpatterns = [
    path('', include(router.urls)),
]
