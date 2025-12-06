from django.db import models
from accounts.models import User, Department

class Course(models.Model):
    title = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='instructed_courses')

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(('Active', 'Active'), ('Dropped', 'Dropped')), default='Active')

    class Meta:
        unique_together = ('student', 'course')


class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=(('Present', 'Present'), ('Absent', 'Absent')))

    class Meta:
        unique_together = ('student', 'course', 'date')


class Grade(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'course')
