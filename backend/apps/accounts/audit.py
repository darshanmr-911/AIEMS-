from apps.accounts.models import AuditLog, StudentProfile


def audit_department_for_user(user):
    if user.department_id:
        return user.department
    profile = StudentProfile.objects.filter(user_id=user.pk).select_related('department').first()
    return profile.department if profile else None


def record_audit(request, action, department=None, target_user=None, details=None, actor=None):
    actor = actor or request.user
    if not getattr(actor, 'is_authenticated', False):
        raise ValueError('Audit events require an authenticated actor.')
    department = department or getattr(request.user, 'department', None)
    if department is None and target_user:
        department = audit_department_for_user(target_user)
    if department is None:
        return
    ip_address = request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        department=department,
        actor=actor,
        target_user=target_user,
        action=action,
        target_type='user' if target_user else '',
        target_id=str(target_user.pk) if target_user else '',
        details=details or {},
        ip_address=ip_address or None,
    )
