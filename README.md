# AIEMS Study Portal

Full-stack college academic resource platform using Django REST Framework and React/Vite.

## Local setup

```bash
cd backend
python3 -m venv ../.venv
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py initialize_department_hods
../.venv/bin/python manage.py runserver
```

Before running `initialize_department_hods`, set the seven department-specific
`INITIAL_HOD_PASSWORD_<DEPARTMENT>` variables through a local secret manager or
environment configuration (`AIML`, `CSE`, `ISE`, `ECE`, `EEE`, `MECH`, and
`CIVIL`). The command creates only missing department HOD accounts, never
replaces an existing password, marks newly created accounts to require a
first-login password change, and prints account email addresses only. Do not put
password values in source control or command logs. Configure SMTP environment
variables to enable password resets.

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## API

JWT authentication, department-scoped HOD endpoints, student endpoints, and
public approved-material access are available under `/api/`.
Use SQLite locally. Configure PostgreSQL in `config/settings.py` for production and keep secrets in environment variables.
