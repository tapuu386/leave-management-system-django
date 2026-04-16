from django.db import models
from apps.accounts.models import User


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True)
    emp_name = models.CharField(max_length=150)
    emp_code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('departments.Department', on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    password_display = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees'

    def __str__(self):
        return f"{self.emp_name} ({self.emp_code})"

    def get_role(self):
        if self.user:
            return self.user.role
        return 'EMPLOYEE'
