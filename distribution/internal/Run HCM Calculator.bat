@echo off
setlocal EnableExtensions

rem Portable-only launcher. Every application path is relative to this folder.
cd /d "%~dp0"
set "PORTABLE_ROOT=%~dp0"
set "BUNDLED_PYTHON=%PORTABLE_ROOT%runtime\python.exe"

if not exist "%BUNDLED_PYTHON%" (
  echo [HCM Calculator] Bundled Python runtime is missing.
  goto :startup_error
)

if not exist "%PORTABLE_ROOT%app\hcmcalc\__init__.py" (
  echo [HCM Calculator] Application files are missing.
  goto :startup_error
)

rem Do not inherit an installed Python environment or user site packages.
set "PYTHONHOME="
set "PYTHONPATH=%PORTABLE_ROOT%app"
set "PYTHONNOUSERSITE=1"
set "PYTHONDONTWRITEBYTECODE=1"

echo Starting HCM Calculator 0.9.0 at http://127.0.0.1:8765/
echo Keep this window open. Press Ctrl+C or close this window to stop.
"%BUNDLED_PYTHON%" -m hcmcalc.api.main --host 127.0.0.1 --port 8765 --open-browser
if errorlevel 1 goto :startup_error

endlocal
exit /b 0

:startup_error
echo.
echo [HCM Calculator] Startup failed.
echo Check the files were extracted completely. If Windows security software blocked the runtime, contact company IT.
pause
endlocal
exit /b 1
