from django.db import models
from apps.employees.models import Employee


class LeaveApplication(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('FULL_LEAVE', 'Full Leave'),
        ('FIRST_HALF', 'First Half'),
        ('SECOND_HALF', 'Second Half'),
        ('ML', 'Medical Leave'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    date_from = models.DateField()
    date_to = models.DateField()
    total_days = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    purpose = models.TextField()
    medical_document = models.FileField(upload_to='medical_docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_leaves'
    )
    action_on = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'leave_applications'
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.employee.emp_name} - {self.leave_type} ({self.date_from} to {self.date_to})"

    def save(self, *args, **kwargs):
        if self.date_from and self.date_to:
            delta = (self.date_to - self.date_from).days + 1
            delta = max(delta, 0)
            if self.leave_type in ('FIRST_HALF', 'SECOND_HALF'):
                self.total_days = delta * 0.5
            else:
                self.total_days = delta
        super().save(*args, **kwargs)
