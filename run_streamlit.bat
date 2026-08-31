@echo off
setlocal
cd /d "%~dp0"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo The local .venv environment is missing. Run setup_app.bat first.
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
echo The legacy Streamlit compatibility UI could not be started.
pause
exit /b 1
