$ErrorActionPreference = "Stop"

try {
    Set-Location -LiteralPath $PSScriptRoot
    $python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $python)) {
        throw "The local .venv environment is missing. Run setup_app.ps1 first."
    }
    & $python -m streamlit run "src\hcmcalc\ui\streamlit_app.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Streamlit could not start. Run setup_app.ps1 to refresh dependencies."
    }
}
catch {
    Write-Host ""
    Write-Host "The legacy Streamlit compatibility UI could not be started. $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
