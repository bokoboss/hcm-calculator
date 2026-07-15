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

## Calculate, save, and export safely

### Language / ภาษา

Choose **English** or **ไทย** in the global language selector. This is a
presentation choice: it does not alter inputs, numerical results, method
identity, or stale-result state. Save files can restore an explicitly saved
language; legacy files retain the active application language. Under **Export /
Report**, choose same-as-UI, English, or Thai. JSON remains machine-readable
with stable keys and values.

Each calculator follows the same compact pattern: choose the calculator, enter
the applicable setup/roadway/traffic/heavy-vehicle inputs, select any supported
advanced adjustments, click **Run calculation**, then review the result and
audit details.

- A result is exportable only while it is marked **Calculated**. If an active
  input or mode changes, it becomes stale and must be recalculated.
- Measured/estimated FFS and internal/external PCE modes hide non-operative
  fields. Those hidden fields do not affect the calculation or freshness.
- **Save project** stores your displayed inputs and, when current, the result
  identity. **Load saved project** clearly reports whether the result is current,
  the project was migrated, or recalculation is required.
- **Export / Report** produces CSV, Excel, Markdown, and report JSON from the
  calculated engine result. `Not predicted` values, including above-capacity
  speed and density where applicable, are not converted to zero.
- **Weaving Segment** is HCM 7.0 only. Use the reference presets as starting
  values or enter a custom isolated freeway weaving case, review the conceptual
  schematic and explicit geometry evidence, then run the calculation. HCM 7.1,
  C-D/multilane weaving, long-segment handoffs, and above-capacity null
  predictions remain visibly guarded.

See the [supported methods matrix](methodology/supported_methods_matrix.md)
before using a workflow outside its documented scope.

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
