from django.contrib import admin
from .models import LeaveApplication

@admin.register(LeaveApplication)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'date_from', 'date_to', 'total_days', 'status')
    list_filter = ('status', 'leave_type')
    search_fields = ('employee__emp_name', 'employee__emp_code')
