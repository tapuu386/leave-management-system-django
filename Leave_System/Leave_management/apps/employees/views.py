from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
import json
from apps.accounts.models import User
from apps.employees.models import Employee
from apps.departments.models import Department


def hr_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ('HR',) and not request.user.is_superuser:
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@hr_required
def hr_dashboard(request):
    from apps.leaves.models import LeaveApplication
    from django.utils import timezone
    today = timezone.now().date()
    total_emp = Employee.objects.filter(is_active=True).count()
    total_dept = Department.objects.count()
    today_leave = LeaveApplication.objects.filter(
        status='APPROVED', date_from__lte=today, date_to__gte=today
    ).count()
    hr_emp = Employee.objects.filter(user=request.user).first()
    pending_leaves = LeaveApplication.objects.filter(employee=hr_emp, status='PENDING').count() if hr_emp else 0
    my_leaves = LeaveApplication.objects.filter(
        employee=hr_emp, status='PENDING'
    ).order_by('-applied_on') if hr_emp else LeaveApplication.objects.none()
    context = {
        'total_emp': total_emp,
        'total_dept': total_dept,
        'today_leave': today_leave,
        'pending_leaves': pending_leaves,
        'my_leaves': my_leaves,
        'today': today,
    }
    return render(request, 'hr/dashboard.html', context)


@hr_required
def add_employee(request):
    """Single employee add (GET form + POST)."""
    departments = Department.objects.all().order_by('dept_name')
    employees   = Employee.objects.filter(is_active=True).order_by('emp_name')

    if request.method == 'POST':
        emp_name    = request.POST.get('emp_name', '').strip()
        emp_code    = request.POST.get('emp_code', '').strip()
        dept_id     = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        email       = request.POST.get('email', '').strip()
        mobile_no   = request.POST.get('mobile_no', '').strip()
        location    = request.POST.get('location', '').strip()
        manager_id  = request.POST.get('manager', '').strip()
        role        = request.POST.get('role', 'EMPLOYEE')

        errors = []
        if not emp_name:    errors.append('Employee name is required.')
        if not emp_code:    errors.append('Employee code is required.')
        if not email:       errors.append('Email is required.')
        if not designation: errors.append('Designation is required.')
        if Employee.objects.filter(emp_code=emp_code).exists():
            errors.append(f'Employee code "{emp_code}" already exists.')
        if Employee.objects.filter(email=email).exists():
            errors.append(f'Email "{email}" already exists.')
        if User.objects.filter(username=emp_code).exists():
            errors.append(f'Username "{emp_code}" already taken.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            with transaction.atomic():
                # username = emp_code (unique & clean), password = emp_code
                user = User.objects.create_user(
                    username=emp_code, password=emp_code,
                    role=role, email=email
                )
                emp = Employee(
                    user=user, emp_name=emp_name, emp_code=emp_code,
                    designation=designation, email=email,
                    mobile_no=mobile_no or None,
                    location=location or None,
                    password_display=emp_code
                )
                if dept_id:
                    try:
                        emp.department = Department.objects.get(pk=dept_id)
                    except Department.DoesNotExist:
                        pass
                if manager_id:
                    try:
                        emp.manager = Employee.objects.get(pk=manager_id)
                    except Employee.DoesNotExist:
                        pass
                emp.save()
                messages.success(
                    request,
                    f'✅ Employee "{emp_name}" added. Username: {emp_code} | Password: {emp_code}'
                )
            return redirect('add_employee')

    return render(request, 'hr/add_employee.html', {
        'departments': departments,
        'employees': employees,
    })


@hr_required
def list_employees(request):
    employees = (
        Employee.objects
        .filter(is_active=True)
        .select_related('department', 'manager', 'user')
        .order_by('emp_name')
    )
    return render(request, 'hr/list_employees.html', {'employees': employees})


@hr_required
def edit_employee(request, emp_id):
    emp          = get_object_or_404(Employee, pk=emp_id)
    departments  = Department.objects.all().order_by('dept_name')
    all_employees = Employee.objects.filter(is_active=True).exclude(pk=emp_id).order_by('emp_name')

    if request.method == 'POST':
        emp.emp_name    = request.POST.get('emp_name', emp.emp_name).strip()
        new_emp_code    = request.POST.get('emp_code', emp.emp_code).strip()
        emp.designation = request.POST.get('designation', emp.designation).strip()
        dept_id         = request.POST.get('department', '').strip()
        manager_id      = request.POST.get('manager', '').strip()
        new_email       = request.POST.get('email', '').strip()
        new_role        = request.POST.get('role', '').strip()
        emp.mobile_no   = request.POST.get('mobile_no', '').strip() or None
        emp.location    = request.POST.get('location', '').strip() or None

        # Validate emp_code uniqueness
        if new_emp_code and new_emp_code != emp.emp_code:
            if Employee.objects.filter(emp_code=new_emp_code).exclude(pk=emp.pk).exists():
                messages.error(request, 'Employee code already exists.')
                return redirect('edit_employee', emp_id=emp_id)
            emp.emp_code = new_emp_code

        if dept_id:
            try:
                emp.department = Department.objects.get(pk=dept_id)
            except Department.DoesNotExist:
                pass
        else:
            emp.department = None

        if manager_id:
            try:
                emp.manager = Employee.objects.get(pk=manager_id)
            except Employee.DoesNotExist:
                pass
        else:
            emp.manager = None

        if new_email:
            emp.email = new_email
        if emp.user:
            if new_role:
                emp.user.role = new_role
            if new_email:
                emp.user.email = new_email
            emp.user.save()
        emp.save()
        messages.success(request, f'Employee "{emp.emp_name}" updated successfully.')
        return redirect('list_employees')

    return render(request, 'hr/edit_employee.html', {
        'emp': emp,
        'departments': departments,
        'all_employees': all_employees,
    })


@hr_required
def deactivate_employee(request, emp_id):
    emp = get_object_or_404(Employee, pk=emp_id)
    if request.method == 'POST':
        emp.is_active = False
        emp.save()
        if emp.user:
            emp.user.is_active = False
            emp.user.save()
        messages.success(request, f'Employee "{emp.emp_name}" deactivated.')
    return redirect('list_employees')


@hr_required
def monthly_report(request):
    from apps.leaves.models import LeaveApplication
    import datetime
    month = request.GET.get('month', datetime.date.today().strftime('%Y-%m'))
    try:
        year, mon = map(int, month.split('-'))
        from django.db.models import Q
        leaves = LeaveApplication.objects.filter(
            status='APPROVED'
        ).filter(
            Q(date_from__year=year, date_from__month=mon) |
            Q(date_to__year=year, date_to__month=mon)
        ).select_related('employee', 'employee__department', 'approved_by').order_by('employee__emp_name')
    except Exception:
        leaves = LeaveApplication.objects.none()
        month = datetime.date.today().strftime('%Y-%m')
    return render(request, 'hr/monthly_report.html', {'leaves': leaves, 'month': month})


@hr_required
def hr_cancel_leave(request):
    from apps.leaves.models import LeaveApplication
    from django.utils import timezone
    today = timezone.now().date()
    approved_leaves = LeaveApplication.objects.filter(
        status='APPROVED', date_from__gte=today
    ).select_related('employee', 'employee__department').order_by('date_from')

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        leave = LeaveApplication.objects.filter(pk=leave_id, status='APPROVED', date_from__gte=today).first()
        if leave:
            leave.status = 'CANCELLED'
            leave.save()
            messages.success(request, f'Leave of "{leave.employee.emp_name}" cancelled.')
        else:
            messages.error(request, 'Leave cannot be cancelled.')
        return redirect('hr_cancel_leave')

    return render(request, 'hr/cancel_leave.html', {'approved_leaves': approved_leaves, 'today': today})


@hr_required
def add_md(request):
    existing_md = User.objects.filter(role='MD').select_related('employee').first()
    departments = Department.objects.all().order_by('dept_name')
    if request.method == 'POST':
        emp_name    = request.POST.get('emp_name', '').strip()
        emp_code    = request.POST.get('emp_code', '').strip()
        email       = request.POST.get('email', '').strip()
        designation = request.POST.get('designation', 'Managing Director').strip()
        password    = request.POST.get('password', '').strip()

        errors = []
        if not emp_name:  errors.append('Name required.')
        if not emp_code:  errors.append('Employee code required.')
        if not email:     errors.append('Email required.')
        if not password:  errors.append('Password required.')
        if Employee.objects.filter(emp_code=emp_code).exists(): errors.append('Employee code already exists.')
        if User.objects.filter(username=emp_code).exists():     errors.append('Username already taken.')

        if errors:
            for e in errors: messages.error(request, e)
        else:
            with transaction.atomic():
                if existing_md:
                    existing_md.role = 'EMPLOYEE'
                    existing_md.save()
                user = User.objects.create_user(
                    username=emp_code, password=password, role='MD', email=email
                )
                Employee.objects.create(
                    user=user, emp_name=emp_name, emp_code=emp_code,
                    designation=designation, email=email, password_display=password
                )
                messages.success(request, f'Managing Director "{emp_name}" added. Username: {emp_code}')
                return redirect('add_md')

    return render(request, 'hr/add_md.html', {
        'existing_md': existing_md,
        'departments': departments,
    })


@hr_required
def create_hr(request):
    if request.method == 'POST':
        emp_name    = request.POST.get('emp_name', '').strip()
        emp_code    = request.POST.get('emp_code', '').strip()
        email       = request.POST.get('email', '').strip()
        designation = request.POST.get('designation', 'HR Manager').strip()
        password    = request.POST.get('password', '').strip()

        errors = []
        if not emp_name:  errors.append('Name required.')
        if not emp_code:  errors.append('Employee code required.')
        if not email:     errors.append('Email required.')
        if not password:  errors.append('Password required.')
        if Employee.objects.filter(emp_code=emp_code).exists(): errors.append('Employee code already exists.')
        if User.objects.filter(username=emp_code).exists():     errors.append('Username already taken.')

        if errors:
            for e in errors: messages.error(request, e)
        else:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=emp_code, password=password,
                    role='HR', email=email, is_staff=True
                )
                Employee.objects.create(
                    user=user, emp_name=emp_name, emp_code=emp_code,
                    designation=designation, email=email, password_display=password
                )
                messages.success(request, f'HR account "{emp_name}" created. Username: {emp_code} | Password: {password}')
                return redirect('create_hr')

    hr_list = Employee.objects.filter(user__role='HR', is_active=True).select_related('user')
    return render(request, 'hr/create_hr.html', {'hr_list': hr_list})
