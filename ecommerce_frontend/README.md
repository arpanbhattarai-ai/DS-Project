# Django Frontend Dashboard

## Purpose
This frontend provides a business dashboard UI for the FastAPI analytics backend.

## Prerequisites
1. Keep this folder as a sibling of `ecommerce_backend`.
2. Install frontend dependencies.
3. Start FastAPI backend on `http://127.0.0.1:8000`.

## Run
From the parent folder that contains both `ecommerce_backend` and `ecommerce_frontend`:

```powershell
cd ecommerce_frontend
..\ecommerce_backend\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\ecommerce_backend\.venv\Scripts\python.exe manage.py migrate
..\ecommerce_backend\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8010
```

Then open `http://127.0.0.1:8010`.

Backend startup (separate terminal):

```powershell
cd ecommerce_backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

## Environment variables
- `FASTAPI_BASE_URL` (default: `http://127.0.0.1:8000`)
- `DASHBOARD_TIMEOUT_SECONDS` (default: `8`)
- `DJANGO_DEBUG` (default: `1`)
- `DJANGO_ALLOWED_HOSTS` (default: `127.0.0.1,localhost`)
