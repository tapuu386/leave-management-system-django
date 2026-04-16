from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('add-employee/', views.add_employee, name='add_employee'),
    path('employees/', views.list_employees, name='list_employees'),
    path('edit-employee/<int:emp_id>/', views.edit_employee, name='edit_employee'),
    path('deactivate-employee/<int:emp_id>/', views.deactivate_employee, name='deactivate_employee'),
    path('monthly-report/', views.monthly_report, name='monthly_report'),
    path('cancel-leave/', views.hr_cancel_leave, name='hr_cancel_leave'),
    path('add-md/', views.add_md, name='add_md'),
    path('create-hr/', views.create_hr, name='create_hr'),
]
