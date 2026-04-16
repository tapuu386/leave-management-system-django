from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError('Username required')
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'HR')
        user = self.create_user(username, password, **extra)
        # Superuser ko Employee list mein automatically add karo
        try:
            from apps.employees.models import Employee
            if not Employee.objects.filter(user=user).exists():
                # Unique emp_code generate karo
                emp_code = f'ADMIN{user.pk:03d}'
                while Employee.objects.filter(emp_code=emp_code).exists():
                    emp_code = f'ADMIN{user.pk:03d}X'
                Employee.objects.create(
                    user=user,
                    emp_name=username,
                    emp_code=emp_code,
                    designation='',
                    email=user.email or f'{username}@admin.com',
                    password_display=password or '',
                )
        except Exception:
            pass
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('HR', 'HR'),
        ('EMPLOYEE', 'Employee'),
        ('DEPT_HEAD', 'Department Head'),
        ('MD', 'Managing Director'),
    ]
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = 'username'

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.role})"
