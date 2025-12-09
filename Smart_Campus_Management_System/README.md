# Smart Campus Management API (Django REST Framework)

## Project Overview

A Django REST Framework backend for campus management with custom users, role-based access, courses, events, notifications, and JWT authentication.

## Features

- Custom user model (email login), departments, groups (admin/teacher/student).
- JWT auth (SimpleJWT) with access/refresh tokens.
- Accounts: login, user CRUD (admin), self-profile access; departments CRUD (admin); groups/permissions (superuser).
- Courses: courses, enrollments, attendance, grades with role-aware permissions.
- Events: create/manage events, self-register/unregister, participant listing.
- Notifications: CRUD, unread counts, mark read/unread, bulk ops; utilities to send notifications from code.

## Tech Stack

- Python, Django, Django REST Framework, SimpleJWT
- SQLite by default (configurable)

## Folder Structure

```
Smart_Campus_Management_System/
├─ Smart_Campus/              # Django project settings/urls
├─ accounts/                  # Custom user, auth, groups, departments
├─ courses/                   # Courses, enrollments, attendance, grades
├─ events/                    # Events and participants
├─ notifications/             # Notifications module & utilities
├─ requirements.txt
└─ manage.py
```

## Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Setup

- Set env vars (or .env) for prod:
  - `SECRET_KEY=...`
  - `DEBUG=False`
  - `ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1`
  - `DATABASE_URL=sqlite:///db.sqlite3` (or your DB)

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Running the Project

```bash
python manage.py runserver
```

## Authentication

- JWT via `Authorization: Bearer <access_token>`
- Token lifetimes (see `SIMPLE_JWT`): access 30m, refresh 7d

### Login

**POST** `/api/accounts/login/`

```json
{ "email": "user@example.com", "password": "secret" }
```

Response (trimmed):

```json
{
  "refresh": "...",
  "access": "...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin",
    "groups": [{ "id": 1, "name": "admin", "permissions": [ ... ] }],
    "permissions": [ ... ],
    "is_staff": true,
    "is_superuser": true
  }
}
```

## API Documentation (selected)

### Accounts

- Users: `GET/POST /api/accounts/users/` (admin); `GET/PATCH/DELETE /api/accounts/users/{id}/` (admin or self for read/update)
- Departments: `GET/POST /api/accounts/departments/` (admin); `GET/PATCH/DELETE /api/accounts/departments/{id}/` (admin)
- Groups: `GET /api/accounts/groups/` (auth); `POST/PATCH/DELETE /api/accounts/groups/{id}/` (superuser)
- Permissions: `GET /api/accounts/permissions/` (auth)

### Courses

- Courses: `GET /api/courses/courses/?department=1&instructor=2`; `POST`/`PATCH`/`DELETE` (teacher/admin); detail `GET`
- Enrollments: `GET /api/courses/enrollments/?course=1&student=2`; `POST` (students self; teacher/admin any); `PATCH`/`DELETE` (teacher/admin)
- Attendance: `GET /api/courses/attendance/?course=1&student=2&date=YYYY-MM-DD`; `POST`/`PATCH`/`DELETE` (teacher/admin)
- Grades: `GET /api/courses/grades/?course=1&student=2`; `POST`/`PATCH`/`DELETE` (teacher/admin)
- Course sub-actions: `GET /api/courses/courses/{id}/enrollments/`, `/attendance/`, `/grades/`

### Events

- Events: `GET /api/events/events/?created_by=1&upcoming=true`; `POST` (auth, creator auto-set); `PATCH`/`DELETE` (creator/teacher/admin); detail `GET`
- Event actions: `GET /api/events/events/{id}/participants/`; `POST/DELETE /api/events/events/{id}/register/` (self-register/unregister)
- Participants: `GET /api/events/participants/?event=1&student=2`; `POST` (students self; teacher/admin any); `PATCH`/`DELETE` (teacher/admin or self)

### Notifications

- Notifications: `GET /api/notifications/notifications/?unread=true`; `POST` (users for self; teacher/admin for any user); detail `GET`; `DELETE`
- Actions: `POST /api/notifications/notifications/{id}/mark_read/`; `mark_unread/`; `POST /api/notifications/notifications/mark_all_read/`; `GET /api/notifications/notifications/unread_count/`; `DELETE /api/notifications/notifications/delete_all_read/`

## End-to-End Flow (example)

1. Admin creates departments, teachers, students; assigns groups.
2. Teacher creates courses; students self-enroll.
3. Teacher records attendance/grades; students view theirs.
4. Events are created; users register; organizers manage.
5. Notifications sent for enrollments, grades, events (via endpoints or utilities).
6. Frontend uses JWT access (30m) and refresh (7d) tokens.

## Testing

```bash
python manage.py test
```

(Add per-app API tests for permissions and core flows.)

## Deployment

- Set `DEBUG=False`, `ALLOWED_HOSTS`, move secrets/env vars out of code.
- Run migrations on deploy.
- Use production server (gunicorn/uvicorn + nginx); enable HTTPS.
- Configure DB, caching, and secure cookies for production.
