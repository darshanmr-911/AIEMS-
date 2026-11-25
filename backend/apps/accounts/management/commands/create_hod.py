from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Deprecated; use initialize_department_hods instead.'

    def handle(self, *args, **options):
        raise CommandError(
            'Single central HOD accounts are no longer supported. '
            'Use initialize_department_hods with INITIAL_HOD_PASSWORD.'
        )
