from django.core.management.base import BaseCommand
from webapp.models import User

class Command(BaseCommand):
    help = 'Create initial users in the database'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin@example.com').exists():
            User.objects.create_superuser('admin@example.com', 'admin@example.com', 'Password1.')

        for username in ['user1@example.com', 'user2@example.com']:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username, username, 'Password1.')

        self.stdout.write(self.style.SUCCESS('Successfully created initial users'))
