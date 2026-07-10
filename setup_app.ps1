$ErrorActionPreference = "Stop"

try {
    Set-Location -LiteralPath $PSScriptRoot
    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

    if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
        throw "Python 3.12 is required. Install it from https://www.python.org/downloads/."
    }
    & py -3.12 --version
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.12 is required. Install it from https://www.python.org/downloads/."
    }

    if (-not (Test-Path -LiteralPath $python)) {
        Write-Host "Creating the local Python 3.12 environment..."
        & py -3.12 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Could not create the local Python environment." }
    }

    & $python -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 12))"
    if ($LASTEXITCODE -ne 0) {
        throw "The existing .venv is not using Python 3.12. Delete the .venv folder, then run setup_app.ps1 again."
    }

    Write-Host "Refreshing calculator dependencies..."
    & $python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Could not upgrade pip." }
    & $python -m pip install -e ".[dev,ui]"
    if ($LASTEXITCODE -ne 0) { throw "Could not install the calculator dependencies." }

    Write-Host "Setup complete. Run run_app.ps1 to open the HCM Calculator."
}
catch {
    Write-Host ""
    Write-Host "Setup could not be completed. $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
