from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create the initial HOD account'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(role=User.Role.HOD).exists():
            self.stdout.write(self.style.WARNING('An HOD account already exists.'))
            return
        if User.objects.filter(username=options['username']).exists():
            raise SystemExit('That username is already in use.')
        User.objects.create_superuser(
            username=options['username'],
            email=options['email'],
            password=options['password'],
            role=User.Role.HOD,
        )
        self.stdout.write(self.style.SUCCESS('HOD account created successfully.'))
