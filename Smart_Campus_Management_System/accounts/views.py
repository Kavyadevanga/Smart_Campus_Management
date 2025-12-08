from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import LoginSerializer, UserSerializer, DepartmentSerializer, GroupSerializer
from rest_framework import viewsets, permissions
from .models import User, Department
from django.contrib.auth.models import Group, Permission
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrSelf(BasePermission):
    """
    Allow admins full access; non-admins can only access their own user.
    """

    def has_permission(self, request, view):
        # Authenticated users can reach object-level checks; creation/listing limited separately.
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj == request.user


class IsSuperUser(BasePermission):
    """
    Permission class to check if user is a superuser.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Get user groups with their permissions
        groups_data = []
        all_permissions_dict = {}  # Use dict to deduplicate by permission id
        
        for group in user.groups.all():
            group_permissions = group.permissions.all()
            permissions_list = []
            for perm in group_permissions:
                perm_data = {
                    'id': perm.id,
                    'codename': perm.codename,
                    'name': perm.name
                }
                permissions_list.append(perm_data)
                # Store in dict to deduplicate
                all_permissions_dict[perm.id] = perm_data
            
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'permissions': permissions_list
            })
        
        # Also include user-specific permissions
        user_permissions = user.user_permissions.all()
        for perm in user_permissions:
            all_permissions_dict[perm.id] = {
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name
            }
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'role': user.groups.first().name if user.groups.exists() else None,
                'groups': groups_data,
                'permissions': list(all_permissions_dict.values()),
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        }, status=status.HTTP_200_OK)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # default; refined per action

    def get_permissions(self):
        # Only admins can create, list, or delete users.
        if self.action in ["create", "list", "destroy"]:
            return [IsAdminUser()]
        # Updates and retrieves: admins or the user themselves.
        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAdminOrSelf()]
        return super().get_permissions()

    # Optional: filter by role/student if you want
    def get_queryset(self):
        user = self.request.user

        # Admins can see everyone; others only themselves.
        if user.is_staff:
            queryset = super().get_queryset()
            role = self.request.query_params.get('role')
            if role:
                queryset = queryset.filter(groups__name=role)
            return queryset

        return super().get_queryset().filter(id=user.id)



class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Groups (admin, teacher, student, etc.)
    Only superusers can create, update, or delete groups.
    All authenticated users can view groups.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSuperUser()]
        return [IsAuthenticated()]


class PermissionListView(APIView):
    """
    List all available permissions in the system.
    Useful for frontend when creating/editing groups.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        permissions = Permission.objects.all().select_related('content_type')
        permissions_data = [
            {
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
                'content_type': perm.content_type.app_label + '.' + perm.content_type.model
            }
            for perm in permissions
        ]
        return Response(permissions_data, status=status.HTTP_200_OK)