from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Sirf EMPLOYEE role ke liye incomplete profile check karo
            if user.role == 'EMPLOYEE':
                try:
                    from apps.employees.models import Employee
                    emp = Employee.objects.get(user=user)
                    if not emp.designation or not emp.department:
                        return redirect('complete_profile')
                except Exception:
                    pass
            return redirect('dashboard_redirect')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_redirect(request):
    role = request.user.role
    if role == 'HR':
        return redirect('hr_dashboard')
    elif role == 'DEPT_HEAD':
        return redirect('depthead_dashboard')
    elif role == 'MD':
        return redirect('md_dashboard')
    else:
        return redirect('employee_dashboard')


@login_required
def complete_profile(request):
    from apps.employees.models import Employee
    from apps.departments.models import Department
    try:
        emp = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return redirect('dashboard_redirect')

    # Already complete hai to redirect karo
    if emp.designation and emp.department:
        return redirect('dashboard_redirect')

    departments = Department.objects.all()
    if request.method == 'POST':
        designation = request.POST.get('designation', '').strip()
        dept_id = request.POST.get('department', '').strip()
        email = request.POST.get('email', '').strip()
        emp_code = request.POST.get('emp_code', '').strip()

        errors = []
        if not designation:
            errors.append('Designation required.')
        if not dept_id:
            errors.append('Department required.')
        if emp_code and emp_code != emp.emp_code:
            if Employee.objects.filter(emp_code=emp_code).exclude(pk=emp.pk).exists():
                errors.append('Employee code already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            if emp_code:
                emp.emp_code = emp_code
            emp.designation = designation
            emp.department = Department.objects.get(pk=dept_id)
            if email:
                emp.email = email
                request.user.email = email
                request.user.save()
            emp.save()
            messages.success(request, 'Profile completed successfully!')
            return redirect('dashboard_redirect')

    return render(request, 'accounts/complete_profile.html', {
        'emp': emp,
        'departments': departments,
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            # Also update emp_code password field if employee
            try:
                from apps.employees.models import Employee
                emp = Employee.objects.get(user=request.user)
                emp.password_display = request.POST.get('new_password1', '')
                emp.save()
            except Exception:
                pass
            messages.success(request, 'Password changed successfully!')
            return redirect('dashboard_redirect')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
