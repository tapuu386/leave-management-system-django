from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import LeaveApplication
from apps.employees.models import Employee
import datetime


def get_employee(user):
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return None


def send_leave_notification(leave, recipients, subject_prefix):
    subject = f"{subject_prefix} - Leave Application by {leave.employee.emp_name}"
    message = (
        f"Employee: {leave.employee.emp_name} ({leave.employee.emp_code})\n"
        f"Department: {leave.employee.department}\n"
        f"Leave Type: {leave.get_leave_type_display()}\n"
        f"From: {leave.date_from} To: {leave.date_to}\n"
        f"Total Days: {leave.total_days}\n"
        f"Purpose: {leave.purpose}\n"
        f"Status: {leave.status}"
    )
    valid = [r for r in recipients if r]
    if valid:
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, valid, fail_silently=True)
        except Exception:
            pass


# ─── EMPLOYEE DASHBOARD ─────────────────────────────────────────────────────

@login_required
def employee_dashboard(request):
    emp = get_employee(request.user)
    if not emp:
        messages.error(request, 'Employee profile not found.')
        return redirect('login')
    today = timezone.now().date()
    pending = LeaveApplication.objects.filter(employee=emp, status='PENDING').count()
    approved = LeaveApplication.objects.filter(employee=emp, status='APPROVED').count()
    on_leave_today = LeaveApplication.objects.filter(
        employee=emp, status='APPROVED', date_from__lte=today, date_to__gte=today
    ).exists()
    recent = LeaveApplication.objects.filter(employee=emp).order_by('-applied_on')[:5]
    # Agar yeh employee kisi ka manager hai, unki pending leaves bhi dikhao
    manager_pending_leaves = LeaveApplication.objects.filter(
        employee__manager=emp, status='PENDING'
    ).select_related('employee', 'employee__department').order_by('-applied_on')

    context = {
        'emp': emp, 'pending': pending, 'approved': approved,
        'on_leave_today': on_leave_today, 'recent': recent, 'today': today,
        'manager_pending_leaves': manager_pending_leaves,
    }
    return render(request, 'employee/dashboard.html', context)


@login_required
def apply_leave(request):
    emp = get_employee(request.user)
    if not emp:
        messages.error(request, 'Employee profile not found. Please complete your profile first.')
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        purpose = request.POST.get('purpose', '').strip()
        doc = request.FILES.get('medical_document')

        errors = []
        try:
            df = datetime.date.fromisoformat(date_from)
            dt = datetime.date.fromisoformat(date_to)
        except Exception:
            errors.append('Invalid dates.')
            df = dt = None

        if leave_type not in ('FULL_LEAVE', 'FIRST_HALF', 'SECOND_HALF', 'ML'):
            errors.append('Invalid leave type.')

        if df and dt:
            if dt < df:
                errors.append('Date To must be after Date From.')

        if leave_type == 'ML' and not doc:
            errors.append('Medical document is required for Medical Leave.')

        if not purpose:
            errors.append('Purpose is required.')

        if errors:
            for e in errors: messages.error(request, e)
        else:
            leave = LeaveApplication(
                employee=emp, leave_type=leave_type,
                date_from=df, date_to=dt, purpose=purpose
            )
            if doc and leave_type == 'ML':
                leave.medical_document = doc
            leave.save()

            recipients = []
            if emp.manager and emp.manager.email:
                recipients.append(emp.manager.email)
            if emp.department and emp.department.dept_head and emp.department.dept_head.email:
                if emp.department.dept_head != emp.manager:
                    recipients.append(emp.department.dept_head.email)
            send_leave_notification(leave, recipients, 'New Leave Application')

            messages.success(request, 'Leave application submitted successfully.')
            return redirect('my_leave_status')

    return render(request, 'employee/apply_leave.html', {'emp': emp})

@login_required
def my_leave_status(request):
    emp = get_employee(request.user)
    if not emp:
        return redirect('login')
    leaves = LeaveApplication.objects.filter(employee=emp).order_by('-applied_on')
    return render(request, 'employee/leave_status.html', {'leaves': leaves, 'emp': emp})


@login_required
def my_leave_history(request):
    emp = get_employee(request.user)
    if not emp:
        return redirect('login')
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    try:
        year, mon = map(int, month.split('-'))
        leaves = LeaveApplication.objects.filter(
            employee=emp, status='APPROVED',
            date_from__year=year, date_from__month=mon
        ).order_by('-date_from')
    except Exception:
        leaves = LeaveApplication.objects.none()
        month = timezone.now().strftime('%Y-%m')
    return render(request, 'employee/leave_history.html', {'leaves': leaves, 'emp': emp, 'month': month})


@login_required
def cancel_leave(request, leave_id):
    """HR can cancel leave only for same-day applications."""
    leave = get_object_or_404(LeaveApplication, pk=leave_id)
    today = timezone.now().date()
    emp = get_employee(request.user)

    can_cancel = False
    if request.user.role == 'HR' and leave.date_from >= today and leave.status == 'PENDING':
        can_cancel = True
    elif emp and leave.employee == emp and leave.date_from >= today and leave.status == 'PENDING':
        can_cancel = True

    if can_cancel:
        leave.status = 'CANCELLED'
        leave.save()
        messages.success(request, 'Leave cancelled.')
    else:
        messages.error(request, 'Cannot cancel this leave.')
    return redirect(request.META.get('HTTP_REFERER', 'employee_dashboard'))


# ─── DEPARTMENT HEAD DASHBOARD ───────────────────────────────────────────────

@login_required
def depthead_dashboard(request):
    if request.user.role != 'DEPT_HEAD':
        return redirect('dashboard_redirect')
    emp = get_employee(request.user)
    if not emp:
        return redirect('login')
    today = timezone.now().date()
    # Employees in this department
    team = Employee.objects.filter(department=emp.department, is_active=True).exclude(pk=emp.pk)
    on_leave = LeaveApplication.objects.filter(
        employee__in=team, status='APPROVED', date_from__lte=today, date_to__gte=today
    )
    from django.db.models import Q
    pending_approvals = LeaveApplication.objects.filter(
        status='PENDING'
    ).filter(
        Q(employee__department=emp.department) |  # dept_head hone ki wajah se same department
        Q(employee__manager=emp)                  # direct manager hone ki wajah se
    ).exclude(employee=emp).distinct().select_related('employee', 'employee__department').order_by('-applied_on')
    context = {
        'emp': emp, 'team': team, 'on_leave': on_leave,
        'pending_approvals': pending_approvals, 'today': today,
    }
    return render(request, 'depthead/dashboard.html', context)


@login_required
def dept_team_list(request):
    if request.user.role != 'DEPT_HEAD':
        return redirect('dashboard_redirect')
    emp = get_employee(request.user)
    if not emp:
        return redirect('login')
    today = timezone.now().date()
    team = Employee.objects.filter(department=emp.department, is_active=True).exclude(pk=emp.pk)
    on_leave_ids = LeaveApplication.objects.filter(
        employee__in=team, status='APPROVED', date_from__lte=today, date_to__gte=today
    ).values_list('employee_id', flat=True)
    context = {'emp': emp, 'team': team, 'on_leave_ids': on_leave_ids}
    return render(request, 'depthead/team_list.html', context)


@login_required
def approve_reject_leave(request, leave_id):
    """Used by manager, dept head, HR and MD to approve/reject."""
    leave = get_object_or_404(LeaveApplication, pk=leave_id)
    approver_emp = get_employee(request.user)
    role = request.user.role

    # ── Authorization check ──────────────────────────────────────────────────
    # Determine karo ki kya yeh user is leave ko approve karne ka haqdar hai:
    #   1. MD  → sab kuch approve kar sakta hai
    #   2. HR  → sab kuch approve kar sakta hai
    #   3. DEPT_HEAD → sirf apne department ki leaves
    #   4. Koi bhi Employee jo is applicant ka direct manager hai
    #      (chahe uska role EMPLOYEE hi kyun na ho)
    # ────────────────────────────────────────────────────────────────────────
    is_authorized = False

    if role == 'MD':
        is_authorized = True
    elif role == 'HR':
        is_authorized = True
    elif role == 'DEPT_HEAD' and approver_emp:
        # Same department ki leave approve kar sakta hai
        if leave.employee.department == approver_emp.department:
            is_authorized = True
        # Ya phir direct manager hai
        if leave.employee.manager == approver_emp:
            is_authorized = True
    elif approver_emp and leave.employee.manager == approver_emp:
        # Koi bhi employee jo is leave applicant ka direct manager hai
        is_authorized = True

    if not is_authorized:
        messages.error(request, 'Access denied. Aap is leave ko approve/reject karne ke authorized nahi hain.')
        return redirect('dashboard_redirect')

    action = request.POST.get('action')
    reason = request.POST.get('reason', '').strip()

    if action == 'APPROVED':
        leave.status = 'APPROVED'
        leave.approved_by = approver_emp
        leave.action_on = timezone.now()
        leave.save()
        send_leave_notification(leave, [leave.employee.email], 'Leave APPROVED')
        messages.success(request, 'Leave approved.')
    elif action == 'REJECTED':
        leave.status = 'REJECTED'
        leave.approved_by = approver_emp
        leave.action_on = timezone.now()
        leave.rejection_reason = reason
        leave.save()
        send_leave_notification(leave, [leave.employee.email], 'Leave REJECTED')
        messages.error(request, 'Leave rejected.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard_redirect'))


# ─── MANAGING DIRECTOR DASHBOARD ─────────────────────────────────────────────

@login_required
def md_dashboard(request):
    if request.user.role != 'MD':
        return redirect('dashboard_redirect')
    today = timezone.now().date()
    all_employees = Employee.objects.filter(is_active=True).select_related('department')
    on_leave_today = LeaveApplication.objects.filter(
        status='APPROVED', date_from__lte=today, date_to__gte=today
    ).select_related('employee', 'employee__department')
    # Sirf unhi employees ki pending leaves dikhao jinka manager MD hai
    md_emp = Employee.objects.filter(user=request.user).first()
    pending_to_md = LeaveApplication.objects.filter(
        status='PENDING', employee__manager=md_emp
    ).select_related('employee', 'employee__department').order_by('-applied_on') if md_emp else LeaveApplication.objects.none()
    context = {
        'all_employees': all_employees,
        'on_leave_today': on_leave_today,
        'pending_to_md': pending_to_md,
        'today': today,
    }
    return render(request, 'md/dashboard.html', context)


# ─── CALENDAR ────────────────────────────────────────────────────────────────

@login_required
def leave_calendar(request):
    import json
    today = timezone.now().date()
    emp = get_employee(request.user)
    role = request.user.role

    if role == 'MD':
        leaves = LeaveApplication.objects.filter(status='APPROVED', date_from__year=today.year)
    elif role == 'HR':
        leaves = LeaveApplication.objects.filter(status='APPROVED', date_from__year=today.year)
    elif role == 'DEPT_HEAD' and emp:
        team = Employee.objects.filter(department=emp.department, is_active=True)
        leaves = LeaveApplication.objects.filter(employee__in=team, status='APPROVED', date_from__year=today.year)
    else:
        leaves = LeaveApplication.objects.filter(employee=emp, status='APPROVED', date_from__year=today.year) if emp else LeaveApplication.objects.none()

    events = []
    for l in leaves:
        events.append({
            'title': f"{l.employee.emp_name} ({l.get_leave_type_display()})",
            'start': str(l.date_from),
            'end': str(l.date_to + datetime.timedelta(days=1)),
            'color': '#4CAF50' if l.leave_type == 'CL' else '#2196F3' if l.leave_type == 'ML' else '#FF9800',
        })
    return render(request, 'common/calendar.html', {'events': json.dumps(events), 'emp': emp})


@login_required
def md_all_employees(request):
    if request.user.role != 'MD':
        return redirect('dashboard_redirect')
    today = timezone.now().date()
    all_employees = Employee.objects.filter(is_active=True).select_related('department', 'manager')
    on_leave_today = LeaveApplication.objects.filter(
        status='APPROVED', date_from__lte=today, date_to__gte=today
    ).values_list('employee_id', flat=True)
    on_leave_ids = set(on_leave_today)
    return render(request, 'md/all_employees.html', {
        'all_employees': all_employees,
        'on_leave_ids': on_leave_ids,
    })
