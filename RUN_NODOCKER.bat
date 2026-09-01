@echo off
cd /d "%~dp0"
echo ============================================================
echo  FaceProof - NO-DOCKER launcher (Python only)
echo  Folder: %~dp0
echo  Needs Python 3.11 installed. No Docker / Node required.
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_nodocker.ps1"
echo.
echo ============================================================
echo  Launcher finished. Two server windows should now be open
echo  (backend + web). App URL:  http://localhost:5173
echo  Keep those two windows open while you use the app.
echo ============================================================
pause
