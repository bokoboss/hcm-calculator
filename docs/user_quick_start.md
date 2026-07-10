# HCM Calculator: Local Quick Start

The HCM Calculator runs locally on your Windows computer and opens in your web
browser. It is not an `.exe`; Python and the project files stay on your
computer while you use the calculator.

## Requirements

- Windows 10 or Windows 11
- Python 3.12 installed from [python.org](https://www.python.org/downloads/)
  with the Python Launcher (`py`) available
- An internet connection on the first run so Python can install the required
  packages

## Exact two-step workflow

1. Open the HCM Calculator project folder in File Explorer.
2. Double-click `setup_app.bat` once for first-time setup, and run it again to
   refresh dependencies after an update.
3. Double-click `run_app.bat` for every normal launch.
4. Streamlit opens the calculator in your default browser. If it does not,
   open the local URL shown in the terminal, usually `http://localhost:8501`.

The normal launch script does not install or upgrade packages. If it reports a
missing Python 3.12 installation or `.venv`, run the setup script after fixing
the stated prerequisite.

## Exact two-step workflow with PowerShell

1. Open PowerShell in the HCM Calculator project folder.
2. Run setup once for first-time setup, and again to refresh dependencies:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\setup_app.ps1
   ```

3. Run this command for every normal launch:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\run_app.ps1
   ```

`Bypass` applies only to that PowerShell session and does not require
administrator rights.

## Stop the app

Return to the terminal window running Streamlit and press `Ctrl+C`. You can
then close the terminal window.

## Troubleshooting

- **`py` is not recognized or Python 3.12 cannot be found:** install Python
  3.12, select the Python Launcher option during installation, then run the
  script again.
- **The browser does not open:** copy the `Local URL` displayed in the
  terminal into a browser, normally `http://localhost:8501`.
- **A script error is displayed:** leave the terminal open and read the error;
  the launch scripts pause after an error so the message remains visible.
- **PowerShell blocks the script:** use the `-ExecutionPolicy Bypass` command
  shown above.
