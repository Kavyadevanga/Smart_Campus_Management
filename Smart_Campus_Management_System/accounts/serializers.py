from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission
from .models import User, Department

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User is inactive.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Both email and password are required.")
        return data

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # optional for update
    email = serializers.EmailField(required=False)  # optional for update

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone', 'department', 'dob', 'gender',
            'roll', 'staff_id', 'password'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model with permissions"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        source='permissions',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids']
    
    def create(self, validated_data):
        permissions = validated_data.pop('permissions', [])
        group = Group.objects.create(**validated_data)
        group.permissions.set(permissions)
        return group
    
    def update(self, instance, validated_data):
        permissions = validated_data.pop('permissions', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance
