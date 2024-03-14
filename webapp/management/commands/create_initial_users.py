from django.core.management.base import BaseCommand
from webapp.models import User

class Command(BaseCommand):
    help = 'Create initial users in the database'

    def handle(self, *args, **options):
        if not User.objects.filter(email='admin1@example.com').exists():
            User.objects.create_superuser('admin1', 'admin1@example.com', 'admin1')

        for username, email, password in [('test11', 'test11@example.com', 'test11'), ('test22', 'test22@example.com', 'test22')]:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username, email, password)

        self.stdout.write(self.style.SUCCESS('Successfully created initial users'))
