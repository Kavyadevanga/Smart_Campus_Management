from rest_framework import serializers
from .models import Course, Enrollment, Attendance, Grade
from accounts.serializers import UserSerializer, DepartmentSerializer
from accounts.models import User, Department


class CourseSerializer(serializers.ModelSerializer):
    department_detail = DepartmentSerializer(source='department', read_only=True)
    instructor_detail = UserSerializer(source='instructor', read_only=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    instructor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = Course
        fields = ['id', 'title', 'code', 'description', 'department', 'department_detail', 
                  'instructor', 'instructor_detail']
        read_only_fields = ['id']


class EnrollmentSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    
    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'student_detail', 'course', 'course_detail', 
                  'enrolled_on', 'status']
        read_only_fields = ['id', 'enrolled_on']
    
    def validate(self, data):
        # Check if enrollment already exists
        if self.instance is None:  # Creating new enrollment
            student = data.get('student')
            course = data.get('course')
            if student and course:
                if Enrollment.objects.filter(student=student, course=course).exists():
                    raise serializers.ValidationError("Student is already enrolled in this course.")
        return data


class AttendanceSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_detail', 'course', 'course_detail', 
                  'date', 'status']
        read_only_fields = ['id']
    
    def validate(self, data):
        # Check if attendance already exists for this student, course, and date
        if self.instance is None:  # Creating new attendance
            student = data.get('student')
            course = data.get('course')
            date = data.get('date')
            if Attendance.objects.filter(student=student, course=course, date=date).exists():
                raise serializers.ValidationError(
                    "Attendance already marked for this student, course, and date."
                )
        return data


class GradeSerializer(serializers.ModelSerializer):
    student_detail = UserSerializer(source='student', read_only=True)
    course_detail = CourseSerializer(source='course', read_only=True)
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    
    class Meta:
        model = Grade
        fields = ['id', 'student', 'student_detail', 'course', 'course_detail', 
                  'score', 'grade', 'remarks']
        read_only_fields = ['id']
    
    def validate_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value
    
    def validate(self, data):
        # Check if grade already exists for this student and course
        if self.instance is None:  # Creating new grade
            student = data.get('student')
            course = data.get('course')
            if Grade.objects.filter(student=student, course=course).exists():
                raise serializers.ValidationError(
                    "Grade already exists for this student and course."
                )
        return data

