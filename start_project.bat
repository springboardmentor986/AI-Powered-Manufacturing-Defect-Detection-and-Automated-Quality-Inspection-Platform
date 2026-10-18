@echo off
title VisionInspect AI - Launching Full Stack Platform
echo ========================================================
echo        Starting VisionInspect AI Platform
echo ========================================================
echo.

:: Check if backend is already running on port 8001
netstat -ano | findstr :8001 | findstr LISTENING > nul
if %errorlevel% equ 0 (
    echo [i] Backend is already running on http://127.0.0.1:8001
) else (
    echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8001 ...
    start "VisionInspect Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"
    timeout /t 3 /nobreak > nul
)

:: Check if frontend is already running on port 5173
netstat -ano | findstr :5173 | findstr LISTENING > nul
if %errorlevel% equ 0 (
    echo [i] Frontend is already running on http://localhost:5173
) else (
    echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
    start "VisionInspect Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
)

echo.
echo ========================================================
echo   VisionInspect AI Platform is Ready!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8001
echo   API Docs: http://127.0.0.1:8001/docs
echo ========================================================
echo.
pause
