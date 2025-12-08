from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q
from django.utils import timezone
from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer


class IsTeacherOrAdmin(BasePermission):
    """
    Permission class to check if user is a teacher or admin.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
        
        return request.user.groups.filter(name='teacher').exists()


class CanManageNotification(BasePermission):
    """
    Permission class for notifications: users can only manage their own notifications.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Users can only access their own notifications
        return obj.user == request.user


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification CRUD operations.
    - Users can only view and manage their own notifications
    - Teachers and Admins can create notifications for any user
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [CanManageNotification]
    
    def get_serializer_class(self):
        if self.action == 'create':
            # Use different serializer for creation if user is admin/teacher
            if self.request.user.is_staff or self.request.user.groups.filter(name='teacher').exists():
                return NotificationCreateSerializer
        return NotificationSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_permissions(self):
        if self.action == 'create':
            # Teachers and admins can create notifications for any user
            # Regular users can create notifications for themselves
            return [IsAuthenticated()]
        return [CanManageNotification()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Users can only see their own notifications
        queryset = queryset.filter(user=user)
        
        # Filter by read status if provided
        read_status = self.request.query_params.get('read_status')
        if read_status is not None:
            read_status_bool = read_status.lower() == 'true'
            queryset = queryset.filter(read_status=read_status_bool)
        
        # Filter unread only
        unread = self.request.query_params.get('unread')
        if unread and unread.lower() == 'true':
            queryset = queryset.filter(read_status=False)
        
        # Order by created_at descending (newest first)
        queryset = queryset.order_by('-created_at')
        
        return queryset.select_related('user')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # If regular user is creating notification, set user to themselves
        if not (user.is_staff or user.groups.filter(name='teacher').exists()):
            serializer.save(user=user)
        else:
            # Teachers/admins can create notifications for any user
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        
        # Ensure user can only mark their own notifications as read
        if notification.user != request.user:
            return Response(
                {'detail': 'You can only mark your own notifications as read.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.read_status = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark a notification as unread"""
        notification = self.get_object()
        
        # Ensure user can only mark their own notifications as unread
        if notification.user != request.user:
            return Response(
                {'detail': 'You can only mark your own notifications as unread.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.read_status = False
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        updated_count = Notification.objects.filter(
            user=request.user,
            read_status=False
        ).update(read_status=True)
        
        return Response({
            'detail': f'Marked {updated_count} notifications as read.',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications for the current user"""
        count = Notification.objects.filter(
            user=request.user,
            read_status=False
        ).count()
        
        return Response({
            'unread_count': count
        })
    
    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """Delete all read notifications for the current user"""
        deleted_count, _ = Notification.objects.filter(
            user=request.user,
            read_status=True
        ).delete()
        
        return Response({
            'detail': f'Deleted {deleted_count} read notifications.',
            'deleted_count': deleted_count
        })
