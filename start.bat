@echo off
echo Starting PQRETS V6.2...

:: Terminal 1: Backend + Database
start "PQRETS Backend" cmd /k "cd /d %~dp0 && docker compose -f docker-compose.dev.yml up"

:: Wait 15 seconds for backend to start
echo Waiting for backend to start...
timeout /t 15 /nobreak > nul

:: Terminal 2: Frontend
start "PQRETS Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

:: Wait 5 seconds for frontend to start
timeout /t 5 /nobreak > nul

:: Open browser
echo Opening browser...
start http://localhost:5174

echo.
echo PQRETS is starting up.
echo Backend:  http://localhost:9000/docs
echo Frontend: http://localhost:5174
echo.
echo Close the two terminal windows to stop the system.
