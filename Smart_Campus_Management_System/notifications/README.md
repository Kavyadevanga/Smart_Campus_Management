# Notifications System

## Overview
The notifications system allows users to receive and manage notifications. Users can only see and manage their own notifications, while teachers and admins can create notifications for any user.

## API Endpoints

### List Notifications
- **GET** `/api/notifications/notifications/`
  - Get all notifications for the current user
  - Query parameters:
    - `read_status=true/false` - Filter by read status
    - `unread=true` - Get only unread notifications

### Get Notification
- **GET** `/api/notifications/notifications/{id}/`
  - Get a specific notification

### Create Notification
- **POST** `/api/notifications/notifications/`
  - Regular users: Creates notification for themselves
  - Teachers/Admins: Can create notifications for any user
  - Body: `{"user": <user_id>, "message": "Your message here"}`

### Mark as Read/Unread
- **POST** `/api/notifications/notifications/{id}/mark_read/` - Mark notification as read
- **POST** `/api/notifications/notifications/{id}/mark_unread/` - Mark notification as unread
- **POST** `/api/notifications/notifications/mark_all_read/` - Mark all notifications as read

### Get Unread Count
- **GET** `/api/notifications/notifications/unread_count/` - Get count of unread notifications

### Delete Notifications
- **DELETE** `/api/notifications/notifications/{id}/` - Delete a notification
- **DELETE** `/api/notifications/notifications/delete_all_read/` - Delete all read notifications

## How to Send Notifications from Other Parts of the System

### Example 1: Send notification when a student enrolls in a course

```python
# In courses/views.py or courses/signals.py
from notifications.utils import create_notification

def enroll_student(course, student):
    # ... enrollment logic ...
    
    # Send notification to student
    create_notification(
        user=student,
        message=f"You have been enrolled in {course.title} (Code: {course.code})"
    )
    
    # Send notification to instructor
    if course.instructor:
        create_notification(
            user=course.instructor,
            message=f"{student.name} has enrolled in your course {course.title}"
        )
```

### Example 2: Send notification when grade is assigned

```python
# In courses/views.py
from notifications.utils import create_notification

def assign_grade(student, course, score, grade):
    # ... grade assignment logic ...
    
    # Send notification to student
    create_notification(
        user=student,
        message=f"Your grade for {course.title} has been updated. Score: {score}, Grade: {grade}"
    )
```

### Example 3: Send notification to all students in a group

```python
# In events/views.py or admin actions
from notifications.utils import create_notification_for_group

def announce_event_to_students(event):
    create_notification_for_group(
        group_name='student',
        message=f"New event: {event.title} on {event.date.strftime('%Y-%m-%d %H:%M')}"
    )
```

### Example 4: Send notification to all users in a department

```python
# In admin actions or department views
from notifications.utils import create_notification_for_department

def announce_to_department(department, message):
    create_notification_for_department(
        department=department,
        message=message
    )
```

### Example 5: Send notification to multiple specific users

```python
# In any view or signal
from notifications.utils import create_notification_for_multiple_users

def notify_course_participants(course, message):
    enrolled_students = course.enrollments.filter(status='Active').values_list('student', flat=True)
    create_notification_for_multiple_users(
        users=list(enrolled_students),
        message=message
    )
```

## Using Django Signals (Recommended)

You can also use Django signals to automatically send notifications:

```python
# In courses/signals.py (create this file)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Enrollment, Grade, Attendance
from notifications.utils import create_notification

@receiver(post_save, sender=Enrollment)
def notify_enrollment(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.student,
            message=f"You have been enrolled in {instance.course.title}"
        )

@receiver(post_save, sender=Grade)
def notify_grade_assigned(sender, instance, created, **kwargs):
    if created:
        create_notification(
            user=instance.student,
            message=f"Your grade for {instance.course.title}: {instance.grade} ({instance.score}%)"
        )

@receiver(post_save, sender=Attendance)
def notify_attendance_marked(sender, instance, created, **kwargs):
    if created and instance.status == 'Absent':
        create_notification(
            user=instance.student,
            message=f"You were marked absent for {instance.course.title} on {instance.date}"
        )
```

Don't forget to register signals in `courses/apps.py`:

```python
class CoursesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'courses'
    
    def ready(self):
        import courses.signals  # noqa
```

## Frontend Integration

### Polling for New Notifications
The frontend can poll the unread count endpoint periodically:

```javascript
// Poll every 30 seconds
setInterval(async () => {
    const response = await fetch('/api/notifications/notifications/unread_count/');
    const data = await response.json();
    if (data.unread_count > 0) {
        // Show notification badge or update UI
        updateNotificationBadge(data.unread_count);
    }
}, 30000);
```

### Real-time Notifications (Future Enhancement)
For real-time notifications, you could integrate:
- Django Channels with WebSockets
- Server-Sent Events (SSE)
- Third-party services like Pusher or Firebase Cloud Messaging

