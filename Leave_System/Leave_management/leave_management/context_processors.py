from apps.leaves.models import LeaveApplication
from apps.employees.models import Employee
from django.db.models import Q


def notifications(request):
    """Inject pending leave notifications for HR, DEPT_HEAD, MD."""
    if not request.user.is_authenticated:
        return {}

    role = request.user.role
    notif_leaves = LeaveApplication.objects.none()

    try:
        if role == 'HR':
            # HR sees all company pending leaves
            notif_leaves = LeaveApplication.objects.filter(
                status='PENDING'
            ).select_related('employee', 'employee__department').order_by('-applied_on')[:15]

        elif role == 'MD':
            # MD sees only their direct reports' pending leaves
            md_emp = Employee.objects.filter(user=request.user).first()
            if md_emp:
                notif_leaves = LeaveApplication.objects.filter(
                    status='PENDING', employee__manager=md_emp
                ).select_related('employee', 'employee__department').order_by('-applied_on')[:15]

        elif role == 'DEPT_HEAD':
            emp = Employee.objects.get(user=request.user)
            notif_leaves = LeaveApplication.objects.filter(
                status='PENDING'
            ).filter(
                Q(employee__department=emp.department) | Q(employee__manager=emp)
            ).exclude(employee=emp).distinct().select_related(
                'employee', 'employee__department'
            ).order_by('-applied_on')[:15]

    except Exception:
        pass

    return {
        'notif_count': notif_leaves.count() if hasattr(notif_leaves, 'count') else 0,
        'notif_leaves': notif_leaves,
    }
