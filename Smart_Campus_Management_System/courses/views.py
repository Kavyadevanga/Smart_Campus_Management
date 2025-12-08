from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.db.models import Q
from .models import Course, Enrollment, Attendance, Grade
from .serializers import CourseSerializer, EnrollmentSerializer, AttendanceSerializer, GradeSerializer


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


class IsInstructorOrAdmin(BasePermission):
    """
    Permission class to check if user is the instructor of the course or admin.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Check if user is the instructor of the course
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        elif hasattr(obj, 'course') and hasattr(obj.course, 'instructor'):
            return obj.course.instructor == request.user
        
        return False


class CanManageAttendance(BasePermission):
    """
    Permission class for attendance: instructors can manage, students can view their own.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Instructors can manage attendance for their courses
        if obj.course.instructor == request.user:
            return True
        
        # Students can only view their own attendance (read-only)
        if request.user.groups.filter(name='student').exists():
            return obj.student == request.user and request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False


class CanManageGrade(BasePermission):
    """
    Permission class for grades: instructors can manage, students can view their own.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True
        
        # Instructors can manage grades for their courses
        if obj.course.instructor == request.user:
            return True
        
        # Students can only view their own grades (read-only)
        if request.user.groups.filter(name='student').exists():
            return obj.student == request.user and request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course CRUD operations.
    - All authenticated users can view courses
    - Teachers and Admins can create, update, delete courses
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by department if provided
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)
        
        # Filter by instructor if provided
        instructor = self.request.query_params.get('instructor')
        if instructor:
            queryset = queryset.filter(instructor_id=instructor)
        
        # Students can only see courses they're enrolled in
        user = self.request.user
        if user.groups.filter(name='student').exists() and not user.is_staff:
            enrolled_courses = Enrollment.objects.filter(
                student=user, 
                status='Active'
            ).values_list('course_id', flat=True)
            queryset = queryset.filter(id__in=enrolled_courses)
        
        return queryset.select_related('department', 'instructor')
    
    @action(detail=True, methods=['get'])
    def enrollments(self, request, pk=None):
        """Get all enrollments for a specific course"""
        course = self.get_object()
        enrollments = Enrollment.objects.filter(course=course)
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get all attendance records for a specific course"""
        course = self.get_object()
        attendance_records = Attendance.objects.filter(course=course)
        
        # Filter by date if provided
        date = request.query_params.get('date')
        if date:
            attendance_records = attendance_records.filter(date=date)
        
        serializer = AttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        """Get all grades for a specific course"""
        course = self.get_object()
        grades = Grade.objects.filter(course=course)
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment CRUD operations.
    - Students can enroll themselves (create) and view their own enrollments
    - Teachers and Admins can manage all enrollments
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create']:
            # Students can enroll themselves, teachers/admins can enroll anyone
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsTeacherOrAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students can only see their own enrollments
        if user.groups.filter(name='student').exists() and not user.is_staff:
            queryset = queryset.filter(student=user)
        
        # Filter by course if provided
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by student if provided (for teachers/admins)
        student = self.request.query_params.get('student')
        if student and (user.is_staff or user.groups.filter(name='teacher').exists()):
            queryset = queryset.filter(student_id=student)
        
        return queryset.select_related('student', 'course')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # If student is creating enrollment, automatically set student to themselves
        if user.groups.filter(name='student').exists() and not user.is_staff:
            serializer.save(student=user)
        else:
            serializer.save()


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Attendance CRUD operations.
    - Students can view their own attendance
    - Teachers (instructors) and Admins can create, update, delete attendance
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [CanManageAttendance]
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsTeacherOrAdmin()]
        return [CanManageAttendance()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students can only see their own attendance
        if user.groups.filter(name='student').exists() and not user.is_staff:
            queryset = queryset.filter(student=user)
        
        # Filter by course if provided
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by student if provided (for teachers/admins)
        student = self.request.query_params.get('student')
        if student and (user.is_staff or user.groups.filter(name='teacher').exists()):
            queryset = queryset.filter(student_id=student)
        
        # Filter by date if provided
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        return queryset.select_related('student', 'course')


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grade CRUD operations.
    - Students can view their own grades
    - Teachers (instructors) and Admins can create, update, delete grades
    """
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [CanManageGrade]
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsTeacherOrAdmin()]
        return [CanManageGrade()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Students can only see their own grades
        if user.groups.filter(name='student').exists() and not user.is_staff:
            queryset = queryset.filter(student=user)
        
        # Filter by course if provided
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        
        # Filter by student if provided (for teachers/admins)
        student = self.request.query_params.get('student')
        if student and (user.is_staff or user.groups.filter(name='teacher').exists()):
            queryset = queryset.filter(student_id=student)
        
        return queryset.select_related('student', 'course')
