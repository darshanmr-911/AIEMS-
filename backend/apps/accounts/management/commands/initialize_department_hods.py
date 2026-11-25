import os

from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.academics.defaults import DEFAULT_DEPARTMENTS
from apps.academics.models import Department


class Command(BaseCommand):
    help = 'Create missing department HOD accounts using INITIAL_HOD_PASSWORD.'

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.environ.get('INITIAL_HOD_PASSWORD')
        if not password:
            raise CommandError('Set INITIAL_HOD_PASSWORD before initializing HOD accounts.')
        try:
            password_validation.validate_password(password)
        except ValidationError as exc:
            raise CommandError(f'INITIAL_HOD_PASSWORD does not meet password requirements: {exc}') from exc

        User = get_user_model()
        created_count = 0
        for code, name, email_prefix in DEFAULT_DEPARTMENTS:
            department, _ = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'email_prefix': email_prefix,
                },
            )
            if department.email_prefix != email_prefix:
                department.email_prefix = email_prefix
                department.save(update_fields=['email_prefix'])

            email = f'hod{department.email_prefix}@aiems.edu.in'
            user = User.objects.filter(email__iexact=email).first()
            if user:
                if user.role != User.Role.HOD:
                    raise CommandError(f'{email} is already assigned to a non-HOD account.')
                if user.department_id not in (None, department.id):
                    raise CommandError(f'{email} is already assigned to another department.')
                if user.department_id is None:
                    user.department = department
                    user.save(update_fields=['department'])
                self.stdout.write(f'Already initialized: {email}')
                continue

            if User.objects.filter(username__iexact=email).exists():
                raise CommandError(f'The HOD username {email} is already in use.')

            user = User(username=email, email=email, role=User.Role.HOD, department=department)
            try:
                password_validation.validate_password(password, user)
            except ValidationError as exc:
                raise CommandError(f'INITIAL_HOD_PASSWORD does not meet password requirements: {exc}') from exc
            user.set_password(password)
            user.must_change_password = True
            user.save()
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created: {email}'))

        self.stdout.write(self.style.SUCCESS(f'Initialization complete. Created {created_count} HOD account(s).'))
