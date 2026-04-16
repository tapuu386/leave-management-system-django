#  Leave Management System

# Features

| Module | HR | Dept Head | Employee | MD |
|---|---|---|---|---|
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Apply Leave | ✓ | ✓ | ✓ | — |
| My Leave Status | ✓ | ✓ | ✓ | — |
| My Leave History | ✓ | ✓ | ✓ | — |
| Leave Calendar | ✓ | ✓ | ✓ | ✓ |
| Add Department | ✓ | — | — | — |
| Add Employee | ✓ | — | — | — |
| All Employees List | ✓ | — | — | ✓ |
| Approve/Reject Leave | ✓ | ✓ | — | ✓ |
| Monthly Report | ✓ | — | — | — |
| Change Password | ✓ | ✓ | ✓ | ✓ |

# Database Tables (Only 4)

| Table | Purpose |
|---|---|
| `users` | Login credentials + roles |
| `employees` | All employee details |
| `departments` | Department + head info |
| `leave_applications` | All leave records |

# Project Structure

leave_management/
├── apps/
│   ├── accounts/       # Login, User model, Change password
│   ├── employees/      # HR views — Add/Edit employee, department, reports
│   ├── departments/    # Department model
│   └── leaves/         # Leave apply, approve, dashboards
├── templates/
│   ├── base.html       # Main layout with sidebar
│   ├── accounts/       # login, change_password
│   ├── hr/             # HR dashboard, department, employee mgmt, reports
│   ├── employee/       # Employee dashboard, apply, status, history
│   ├── depthead/       # Dept head dashboard
│   ├── md/             # MD dashboard
│   └── common/         # Calendar
├── static/             # CSS, JS, images
├── media/              # Uploaded medical documents
├── .env                # Environment config
├── requirements.txt
└── manage.py
```
# Roles & Access

- **HR** — Full system access. Creates employees with temp credentials.
- **Employee** — Apply leave, view status/history, calendar.
- **Department Head** — All employee features + approve/reject team leaves.
- **Managing Director** — View all employees, today's leave status, approve/reject.

# Email Notifications
- When employee applies leave → Email to dept head + manager
- When leave approved/rejected → Email to employee
- Configure Gmail App Password in `.env`
