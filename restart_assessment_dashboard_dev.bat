@echo off
setlocal

REM Restart PQRETS Assessment Dashboard local development environment.
REM This rebuilds the backend Docker image/container and restarts the Vite frontend.

cd /d "%~dp0"

echo [1/4] Rebuilding and restarting backend Docker container...
docker compose -f docker-compose.dev.yml --env-file .env.dev up -d --build backend
if errorlevel 1 (
  echo.
  echo Backend rebuild failed. Please check Docker Desktop/Rancher Desktop and the logs above.
  pause
  exit /b 1
)

echo.
echo [2/4] Stopping old frontend dev server on port 5174 if it exists...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 5174 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo.
echo [3/4] Starting frontend dev server...
start "PQRETS Frontend 5174" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

echo.
echo [4/4] Opening browser...
timeout /t 5 /nobreak >nul
start "" "http://localhost:5174/?reload=%RANDOM%"

echo.
echo Done.
echo Backend API: http://localhost:9000/api/v1/health
echo Frontend:    http://localhost:5174/
echo.
pause
