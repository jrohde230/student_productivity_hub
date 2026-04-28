# Student Productivity Hub

A Django web app for students (and teachers) to manage courses, assignments, projects, learning resources, and calendar events in one place.

## Core Features

- Authentication with email login + signup
- Dashboard with:
  - Quick access feature cards
  - Month-grid calendar
  - Assignment due-date visibility
- Courses:
  - Course list with selectable detail view
  - Textbook linking per course
  - Instructor details
- Assignments:
  - Two-column list/detail layout
  - Sorting, edit, delete
- Projects:
  - Two-column list/detail layout
  - Links management
  - Collaboration (invite/remove collaborators by email)
  - Discussion/comments
- Learning Resources:
  - Three named columns
  - Drag-and-drop ordering within a column
- Cross-object features (polymorphic):
  - Notes
  - Tags
  - Checklists (where supported)
  - Attachments
- Profile:
  - Change username
  - Change password
- Notifications:
  - Upcoming assignment due dates from navbar modal

## Tech Stack

- Python
- Django
- SQLite (default)
- Server-rendered templates with small vanilla JavaScript interactions

## Project Apps

- `core` - dashboard, shared views/context
- `users` - auth-related pages and profile
- `courses`
- `assignments`
- `projects`
- `resources`
- `user_calendar`
- `notes`
- `tags`
- `checklists`
- `attachments`

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run migrations.
4. Create an admin user.
5. Start the dev server.

### Example (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install django
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:

- App: <http://127.0.0.1:8000/>
- Admin: <http://127.0.0.1:8000/admin/>

## Useful Commands

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

## Notes

- Uploaded files are stored under `media/` in development.
- Admin is configured with model registrations and list/search/filter tooling for key objects.