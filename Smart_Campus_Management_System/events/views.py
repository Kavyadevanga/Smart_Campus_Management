from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q
from .models import Event, EventParticipants
from .serializers import EventSerializer, EventParticipantsSerializer


class IsTeacherOrAdmin(BasePermission):
    """
    Permission class to check if user is a teacher or admin.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user is staff/admin or belongs to 'teacher' group
        if request.user.is_staff:
            return True
        
        # Check if user belongs to teacher group
        return request.user.groups.filter(name='teacher').exists()


class CanManageEvent(BasePermission):
    """
    Permission class for events: creators, teachers, and admins can manage.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Teachers can manage events
        if request.user.groups.filter(name='teacher').exists():
            return True
        
        # Event creator can manage their own events
        if obj.created_by == request.user:
            return True
        
        # Others can only view (read-only)
        return request.method in ['GET', 'HEAD', 'OPTIONS']


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event CRUD operations.
    - All authenticated users can view events
    - Teachers, Admins, and event creators can create, update, delete events
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [CanManageEvent]
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]  # Any authenticated user can create events
        return [CanManageEvent()]
    
    def get_serializer_context(self):
        """Add request to serializer context for auto-setting created_by"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by created_by if provided
        created_by = self.request.query_params.get('created_by')
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Filter upcoming/past events
        upcoming = self.request.query_params.get('upcoming')
        if upcoming and upcoming.lower() == 'true':
            from django.utils import timezone
            queryset = queryset.filter(date__gte=timezone.now())
        
        past = self.request.query_params.get('past')
        if past and past.lower() == 'true':
            from django.utils import timezone
            queryset = queryset.filter(date__lt=timezone.now())
        
        # Students can see all events (they can participate)
        # Teachers/Admins can see all events
        
        return queryset.select_related('created_by').prefetch_related('participants')
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Get all participants for a specific event"""
        event = self.get_object()
        participants = EventParticipants.objects.filter(event=event)
        serializer = EventParticipantsSerializer(participants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'])
    def register(self, request, pk=None):
        """Register or unregister current user for an event"""
        event = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            # Register user for event
            if EventParticipants.objects.filter(student=user, event=event).exists():
                return Response(
                    {'detail': 'You are already registered for this event.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            EventParticipants.objects.create(student=user, event=event)
            return Response(
                {'detail': 'Successfully registered for the event.'},
                status=status.HTTP_201_CREATED
            )
        
        elif request.method == 'DELETE':
            # Unregister user from event
            participation = EventParticipants.objects.filter(student=user, event=event).first()
            if not participation:
                return Response(
                    {'detail': 'You are not registered for this event.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            participation.delete()
            return Response(
                {'detail': 'Successfully unregistered from the event.'},
                status=status.HTTP_200_OK
            )


class CanManageParticipation(BasePermission):
    """
    Permission class for event participations: students can manage their own, teachers/admins can manage all.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admins and teachers can manage all participations
        if request.user.is_staff or request.user.groups.filter(name='teacher').exists():
            return True
        
        # Students can only manage their own participations
        return obj.student == request.user


class EventParticipantsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EventParticipants CRUD operations.
    - Students can view their own participations and register/unregister
    - Teachers and Admins can manage all participations
    """
    queryset = EventParticipants.objects.all()
    serializer_class = EventParticipantsSerializer
    permission_classes = [CanManageParticipation]
    
    def get_permissions(self):
        if self.action in ['create']:
            # Any authenticated user can create participations (for themselves)
            return [IsAuthenticated()]
        return [CanManageParticipation()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students can only see their own participations
        if user.groups.filter(name='student').exists() and not user.is_staff:
            queryset = queryset.filter(student=user)
        
        # Filter by event if provided
        event = self.request.query_params.get('event')
        if event:
            queryset = queryset.filter(event_id=event)
        
        # Filter by student if provided (for teachers/admins)
        student = self.request.query_params.get('student')
        if student and (user.is_staff or user.groups.filter(name='teacher').exists()):
            queryset = queryset.filter(student_id=student)
        
        return queryset.select_related('student', 'event')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # If student is creating participation, automatically set student to themselves
        if user.groups.filter(name='student').exists() and not user.is_staff:
            # Check if student field is provided and matches the user
            student = serializer.validated_data.get('student')
            if student and student != user:
                # Only allow if user is admin/teacher
                if not (user.is_staff or user.groups.filter(name='teacher').exists()):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You can only register yourself for events.")
            serializer.save(student=user)
        else:
            serializer.save()
