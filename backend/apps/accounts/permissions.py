from rest_framework.permissions import BasePermission
from .models import TeacherProfile


class IsHod(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_hod()
            and request.user.department_id
            and not request.user.must_change_password
        )


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_teacher()
            and request.user.department_id
            and TeacherProfile.objects.filter(
                user=request.user,
                department_id=request.user.department_id,
            ).exists()
            and not request.user.must_change_password
        )


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_student()
            and request.user.is_active
            and not request.user.must_change_password
        )


class IsAuthenticatedAndPasswordChanged(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and not request.user.must_change_password
        )
