from rest_framework import serializers
from .models import Notification
from accounts.serializers import UserSerializer
from accounts.models import User


class NotificationSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'user_detail', 'message', 'read_status', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # If user is not provided, set it to the current user
        request = self.context.get('request')
        if request and request.user and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications (used by admins/teachers)"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Notification
        fields = ['user', 'message']
    
    def create(self, validated_data):
        return Notification.objects.create(**validated_data)

