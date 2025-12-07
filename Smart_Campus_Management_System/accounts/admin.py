# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, Department

# Custom forms
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'name', 'is_staff', 'is_active')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'name', 'is_staff', 'is_active')

# Custom UserAdmin
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'name', 'department', 'roll', 'staff_id')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Department)
