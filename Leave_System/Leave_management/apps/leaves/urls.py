from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('apply-leave/', views.apply_leave, name='apply_leave'),
    path('my-leave-status/', views.my_leave_status, name='my_leave_status'),
    path('my-leave-history/', views.my_leave_history, name='my_leave_history'),
    path('cancel-leave/<int:leave_id>/', views.cancel_leave, name='cancel_leave'),
    path('approve-reject/<int:leave_id>/', views.approve_reject_leave, name='approve_reject_leave'),
    path('depthead/', views.depthead_dashboard, name='depthead_dashboard'),
    path('depthead/team/', views.dept_team_list, name='dept_team_list'),
    path('md/', views.md_dashboard, name='md_dashboard'),
    path('md/all-employees/', views.md_all_employees, name='md_all_employees'),
    path('calendar/', views.leave_calendar, name='leave_calendar'),
]
