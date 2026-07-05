@echo off
echo =================================================================
echo                    Launching Suproc Agent System
echo =================================================================
echo.
echo Starting FastAPI Backend Server on http://localhost:8000...
start cmd /k "cd backend && python -m uvicorn app:app --reload --port 8000"

echo.
echo Starting Vite React Frontend Dashboard on http://localhost:5173...
start cmd /k "cd frontend && npm run dev"

echo.
echo Launch sequence complete. Please open http://localhost:5173 in your browser.
echo =================================================================
pause
