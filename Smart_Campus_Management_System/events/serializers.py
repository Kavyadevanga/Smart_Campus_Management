from rest_framework import serializers
from .models import Event, EventParticipants
from accounts.serializers import UserSerializer
from accounts.models import User


class EventSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        required=False, 
        allow_null=True
    )
    participants_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = ['id', 'title', 'description', 'created_by', 'created_by_detail', 
                  'date', 'participants_count']
        read_only_fields = ['id']
    
    def get_participants_count(self, obj):
        """Get the count of participants for this event"""
        return obj.participants.count()
    
    def create(self, validated_data):
        # Automatically set created_by to the current user if not provided
        request = self.context.get('request')
        if request and request.user and not validated_data.get('created_by'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class EventParticipantsSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    event_detail = EventSerializer(source='event', read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    
    class Meta:
        model = EventParticipants
        fields = ['id', 'student', 'student_detail', 'event', 'event_detail']
        read_only_fields = ['id']
    
    def validate(self, data):
        # Check if participant already exists
        if self.instance is None:  # Creating new participation
            student = data.get('student')
            event = data.get('event')
            if student and event:
                if EventParticipants.objects.filter(student=student, event=event).exists():
                    raise serializers.ValidationError(
                        "Student is already registered for this event."
                    )
        return data

