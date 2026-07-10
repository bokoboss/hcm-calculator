@echo off
setlocal

rem Run from this script's directory, even when launched by double-clicking.
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 is required. Install it from https://www.python.org/downloads/
  echo, then run setup_app.bat.
  goto :error
)

if not exist "%PYTHON%" (
  echo The local .venv environment is missing.
  echo Run setup_app.bat from this folder, then launch the app again.
  goto :error
)

"%PYTHON%" -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))"
if errorlevel 1 (
  echo The local .venv is not using Python 3.12.
  echo Run setup_app.bat to refresh it. If this continues, delete .venv and run setup_app.bat.
  goto :error
)

"%PYTHON%" -m streamlit run "src\hcmcalc\ui\streamlit_app.py"
if errorlevel 1 (
  echo Streamlit could not start. Run setup_app.bat to refresh dependencies.
  goto :error
)

endlocal
exit /b 0

:error
echo.
echo The HCM Calculator could not be started. Review the message above.
pause
exit /b 1
