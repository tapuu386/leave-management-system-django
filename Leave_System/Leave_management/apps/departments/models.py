from django.db import models


class Department(models.Model):
    dept_name = models.CharField(max_length=100, unique=True)
    dept_head = models.ForeignKey(
        'employees.Employee', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_department'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return self.dept_name
