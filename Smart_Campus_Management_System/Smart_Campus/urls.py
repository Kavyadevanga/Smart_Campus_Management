from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # User authentication and profiles
    path('api/accounts/', include('accounts.urls')),

    # Courses and enrollments
    path('api/courses/', include('courses.urls')),

    # Events
    path('api/events/', include('events.urls')),

    # Notifications (optional)
    path('api/notifications/', include('notifications.urls')),
]
