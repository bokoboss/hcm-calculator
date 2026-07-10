$ErrorActionPreference = "Stop"

try {
    Set-Location -LiteralPath $PSScriptRoot

    if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
        Write-Host "Creating local Python environment..."
        py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Could not create the Python environment." }
    }

    . ".\\.venv\\Scripts\\Activate.ps1"
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }

    python -m pip install -e ".[ui]"
    if ($LASTEXITCODE -ne 0) { throw "Could not install the calculator UI dependencies." }

    python -m streamlit run "src\\hcmcalc\\ui\\streamlit_app.py"
    if ($LASTEXITCODE -ne 0) { throw "Streamlit exited with an error." }
}
catch {
    Write-Host ""
    Write-Host "The HCM Calculator could not be started. $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
