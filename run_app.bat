@echo off
setlocal

rem Run from this script's directory, even when launched by double-clicking.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  py -3.12 -m venv .venv
  if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install -e ".[ui]"
if errorlevel 1 goto :error

python -m streamlit run "src\hcmcalc\ui\streamlit_app.py"
if errorlevel 1 goto :error

endlocal
exit /b 0

:error
echo.
echo The HCM Calculator could not be started. Review the message above.
pause
exit /b 1
