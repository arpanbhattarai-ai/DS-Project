@echo off
setlocal EnableExtensions

REM Resolve workspace root from this script location.
set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%ecommerce_backend"
set "FRONTEND_DIR=%ROOT_DIR%ecommerce_frontend"

set "BACKEND_PY=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "FRONTEND_PY=%FRONTEND_DIR%\env\Scripts\python.exe"

if not exist "%BACKEND_DIR%" (
  echo [ERROR] Backend folder not found: %BACKEND_DIR%
  exit /b 1
)

if not exist "%FRONTEND_DIR%" (
  echo [ERROR] Frontend folder not found: %FRONTEND_DIR%
  exit /b 1
)

if not exist "%BACKEND_PY%" (
  echo [INFO] Backend virtual environment missing. Creating .venv...
  py -m venv "%BACKEND_DIR%\.venv"
  if errorlevel 1 (
    echo [ERROR] Failed to create backend virtual environment.
    exit /b 1
  )
)

if not exist "%FRONTEND_PY%" (
  echo [INFO] Frontend virtual environment missing. Creating env...
  py -m venv "%FRONTEND_DIR%\env"
  if errorlevel 1 (
    echo [ERROR] Failed to create frontend virtual environment.
    exit /b 1
  )
)

echo [INFO] Installing backend requirements...
"%BACKEND_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Backend dependencies installation failed.
  exit /b 1
)

echo [INFO] Installing frontend requirements...
"%FRONTEND_PY%" -m pip install -r "%FRONTEND_DIR%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Frontend dependencies installation failed.
  exit /b 1
)

echo [INFO] Running frontend migrations...
pushd "%FRONTEND_DIR%"
"%FRONTEND_PY%" manage.py migrate
if errorlevel 1 (
  popd
  echo [ERROR] Frontend migration failed.
  exit /b 1
)
popd

echo [INFO] Releasing ports 8002 and 8010 (if already in use)...
for %%P in (8002 8010) do (
  for /f "tokens=5" %%A in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /PID %%A /F >nul 2>&1
  )
)

echo [INFO] Starting backend API on http://127.0.0.1:8002 ...
start "Ecommerce Backend" /D "%BACKEND_DIR%" cmd /k ""%BACKEND_PY%" -m uvicorn main:app --reload --host 127.0.0.1 --port 8002"

echo [INFO] Starting frontend dashboard on http://127.0.0.1:8010 ...
set "FASTAPI_BASE_URL=http://127.0.0.1:8002"
start "Ecommerce Frontend" /D "%FRONTEND_DIR%" cmd /k ""%FRONTEND_PY%" manage.py runserver 127.0.0.1:8010"

echo [DONE] Both servers are launching in separate windows.
exit /b 0
