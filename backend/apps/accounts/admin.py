from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, StudentProfile, TeacherProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'department',
        'is_active',
        'must_change_password',
    )
    list_filter = ('role', 'department', 'is_active', 'must_change_password')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('AIEMS access', {'fields': ('role', 'department', 'must_change_password', 'phone')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('AIEMS access', {'fields': ('role', 'department', 'must_change_password')}),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'designation')
    list_filter = ('department', 'designation')
    search_fields = ('employee_id', 'user__email', 'user__first_name', 'user__last_name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('usn', 'user', 'department', 'semester')
    list_filter = ('department', 'semester')
    search_fields = ('usn', 'user__email', 'user__first_name', 'user__last_name')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'department', 'actor', 'action', 'target_type', 'target_id')
    list_filter = ('department', 'action')
    readonly_fields = (
        'department',
        'actor',
        'target_user',
        'action',
        'target_type',
        'target_id',
        'details',
        'ip_address',
        'created_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
