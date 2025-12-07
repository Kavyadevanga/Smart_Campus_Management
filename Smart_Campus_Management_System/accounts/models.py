from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    head = models.ForeignKey(
        'User', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='headed_departments'
    )

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.head:
            self.head.department = self
            self.head.save()


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):

    username = None  # remove default username

    # Academic details
    roll = models.IntegerField(unique=True, null=True, blank=True)
    staff_id = models.IntegerField(unique=True, null=True, blank=True)

    # Personal info
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)

    # Login config
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email}"
