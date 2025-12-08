"""
Utility functions for creating notifications that can be used throughout the application.
"""
from .models import Notification
from accounts.models import User


def create_notification(user, message, read_status=False):
    """
    Create a notification for a specific user.
    
    Args:
        user: User instance or user ID
        message: Notification message (string)
        read_status: Boolean, default False
    
    Returns:
        Notification instance
    """
    if isinstance(user, int):
        user = User.objects.get(id=user)
    
    return Notification.objects.create(
        user=user,
        message=message,
        read_status=read_status
    )


def create_notification_for_multiple_users(users, message, read_status=False):
    """
    Create notifications for multiple users at once.
    
    Args:
        users: List of User instances or user IDs
        message: Notification message (string)
        read_status: Boolean, default False
    
    Returns:
        List of Notification instances
    """
    notifications = []
    for user in users:
        if isinstance(user, int):
            user = User.objects.get(id=user)
        notifications.append(
            Notification(user=user, message=message, read_status=read_status)
        )
    
    return Notification.objects.bulk_create(notifications)


def create_notification_for_group(group_name, message, read_status=False):
    """
    Create notifications for all users in a specific group.
    
    Args:
        group_name: Name of the group (e.g., 'student', 'teacher', 'admin')
        message: Notification message (string)
        read_status: Boolean, default False
    
    Returns:
        List of Notification instances
    """
    from django.contrib.auth.models import Group
    
    try:
        group = Group.objects.get(name=group_name)
        users = group.user_set.all()
        return create_notification_for_multiple_users(users, message, read_status)
    except Group.DoesNotExist:
        return []


def create_notification_for_department(department, message, read_status=False):
    """
    Create notifications for all users in a specific department.
    
    Args:
        department: Department instance or department ID
        message: Notification message (string)
        read_status: Boolean, default False
    
    Returns:
        List of Notification instances
    """
    from accounts.models import Department
    
    if isinstance(department, int):
        department = Department.objects.get(id=department)
    
    users = department.users.all()
    return create_notification_for_multiple_users(users, message, read_status)

