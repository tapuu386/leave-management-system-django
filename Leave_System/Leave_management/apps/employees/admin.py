from django.contrib import admin
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('emp_name', 'emp_code', 'department', 'designation', 'email', 'is_active')
    search_fields = ('emp_name', 'emp_code', 'email')
    list_filter = ('department', 'is_active')
