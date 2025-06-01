from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'role', 'is_staff')
    list_filter = ('role', 'department', 'is_staff')
    ordering = ('email',)
    search_fields = ('email', 'full_name', 'phone_number')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Персональні дані', {
            'fields': ('full_name', 'phone_number', 'department', 'position', 'photo')
        }),
        ('Права доступу', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Дати', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'phone_number', 'department', 'position', 'role', 'photo', 'is_staff', 'is_superuser')}
        ),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Department)
