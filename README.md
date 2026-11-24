# AIEMS Study Portal

Full-stack college academic resource platform using Django REST Framework and React/Vite.

## Local setup

```bash
cd backend
python3 -m venv ../.venv
../.venv/bin/pip install -r requirements.txt
../.venv/bin/python manage.py migrate
../.venv/bin/python manage.py create_hod --username admin --email admin@aiems.edu --password 'ChangeMe123!'
../.venv/bin/python manage.py runserver
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## API

JWT authentication, role-protected HOD, teacher, and student endpoints are available under `/api/`.
Use SQLite locally. Configure PostgreSQL in `config/settings.py` for production and keep secrets in environment variables.
