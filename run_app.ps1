$ErrorActionPreference = "Stop"

try {
    Set-Location -LiteralPath $PSScriptRoot
    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "Python 3.12 is required. Install it from https://www.python.org/downloads/, then run setup_app.ps1."
    }
    & py -3.12 --version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.12 is required. Install it from https://www.python.org/downloads/, then run setup_app.ps1."
    }

    if (-not (Test-Path -LiteralPath $python)) {
        throw "The local .venv environment is missing. Run setup_app.ps1 from this folder, then launch the app again."
    }

    & $python -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))"
    if ($LASTEXITCODE -ne 0) {
        throw "The local .venv is not using Python 3.12. Run setup_app.ps1 to refresh it. If this continues, delete .venv and run setup_app.ps1."
    }

    & $python -m streamlit run "src\hcmcalc\ui\streamlit_app.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Streamlit could not start. Run setup_app.ps1 to refresh dependencies."
    }
}
catch {
    Write-Host ""
    Write-Host "The HCM Calculator could not be started. $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
