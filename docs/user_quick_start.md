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

## Launch with the batch file

1. Open the HCM Calculator project folder in File Explorer.
2. Double-click `run_app.bat`.
3. On the first run, wait while it creates a local `.venv` folder and installs
   the calculator's UI dependencies.
4. Streamlit opens the calculator in your default browser. If it does not,
   open the local URL shown in the terminal, usually `http://localhost:8501`.

## Launch with PowerShell

1. Open PowerShell in the HCM Calculator project folder.
2. Run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\run_app.ps1
   ```

   `Bypass` applies only to that PowerShell session and does not require
   administrator rights.

## First run

The first run takes longer because the script creates `.venv`, upgrades pip,
and installs the Streamlit UI dependency. Later launches reuse that local
environment.

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
