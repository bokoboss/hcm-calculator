@echo off
setlocal

rem Run from this script's directory, even when launched by double-clicking.
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

py -3.12 --version
if errorlevel 1 (
  echo Python 3.12 is required. Install it from https://www.python.org/downloads/
  goto :error
)

if not exist "%PYTHON%" (
  echo Creating the local Python 3.12 environment...
  py -3.12 -m venv .venv
  if errorlevel 1 goto :error
)

"%PYTHON%" -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))"
if errorlevel 1 (
  echo The existing .venv is not using Python 3.12.
  echo Delete the .venv folder, then run setup_app.bat again.
  goto :error
)

echo Refreshing calculator dependencies...
"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%PYTHON%" -m pip install -e ".[dev,ui]"
if errorlevel 1 goto :error

echo Setup complete. Run run_app.bat to open the HCM Calculator.
endlocal
exit /b 0

:error
echo.
echo Setup could not be completed. Review the message above and try again.
pause
exit /b 1
