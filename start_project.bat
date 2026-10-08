@echo off
title VisionInspect AI - Launching Full Stack Platform
echo ========================================================
echo        Starting VisionInspect AI (Milestone 1)
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "VisionInspect Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
start "VisionInspect Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo   VisionInspect AI is running!
echo   Frontend: http://localhost:5173
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause
