from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.employees.models import Employee


class Command(BaseCommand):
    help = 'Create initial HR user'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='hr_admin')
        parser.add_argument('--password', default='hr@123')
        parser.add_argument('--email', default='hr@company.com')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists.'))
            return

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role='HR',
            is_staff=True
        )
        Employee.objects.create(
            user=user,
            emp_name=username,
            emp_code='HR001',
            designation='HR Manager',
            email=email,
            password_display=password
        )
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ HR user created!\n'
            f'   Username : {username}\n'
            f'   Password : {password}\n'
            f'   Role     : HR\n'
            f'\nLogin at: http://127.0.0.1:8000/accounts/login/\n'
        ))
