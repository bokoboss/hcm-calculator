[CmdletBinding()]
param(
    [string]$OutputRoot = "",
    [string]$DeveloperPython = "",
    [switch]$AllowDirty,
    [switch]$SkipPortableSmoke
)

$ErrorActionPreference = "Stop"

function Get-FullPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$BasePath
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }
    return [System.IO.Path]::GetFullPath((Join-Path $BasePath $Path))
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Remove-GeneratedPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$OutputPath
    )

    $full = [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
    $output = [System.IO.Path]::GetFullPath($OutputPath).TrimEnd('\')
    if (-not $full.StartsWith($output + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a path outside the generated output root: $full"
    }
    if (Test-Path -LiteralPath $full) {
        Remove-Item -LiteralPath $full -Recurse -Force
    }
}

$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$runtimePinPath = Join-Path $repoRoot "distribution\internal\runtime-pin.json"
$runtimeRequirementsPath = Join-Path $repoRoot "distribution\internal\runtime-requirements.txt"
$launcherTemplate = Join-Path $repoRoot "distribution\internal\Run HCM Calculator.bat"
$readmeTemplate = Join-Path $repoRoot "distribution\internal\README-TH.txt"
$versionTemplate = Join-Path $repoRoot "distribution\internal\VERSION.txt"
$pruneScript = Join-Path $repoRoot "scripts\prune_internal_portable.py"
$manifestScript = Join-Path $repoRoot "scripts\generate_internal_portable_manifests.py"
$validatorScript = Join-Path $repoRoot "scripts\validate_internal_portable.py"
$zipScript = Join-Path $repoRoot "scripts\create_deterministic_zip.py"

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $outputRoot = Join-Path $repoRoot ".tmp\internal-portable"
} else {
    $outputRoot = Get-FullPath -Path $OutputRoot -BasePath $repoRoot
}
$outputRoot = [System.IO.Path]::GetFullPath($outputRoot)
[System.IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$repoFull = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\')
if ($outputRoot.TrimEnd('\').Equals($repoFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "OutputRoot must not be the repository root."
}

$artifactName = "HCM-Calculator-v0.9.0-Internal-Windows-x64"
$zipName = "$artifactName.zip"
$buildRoot = Join-Path $outputRoot "build"
$stageRoot = Join-Path $buildRoot $artifactName
$wheelOutput = Join-Path $buildRoot "wheel"
$runtimeExtract = Join-Path $buildRoot "runtime-extract"
$packageCache = Join-Path $buildRoot "package-cache"
$cacheRoot = Join-Path $outputRoot "cache"
$archivePath = Join-Path $cacheRoot "cpython-3.12.14+20260814-x86_64-pc-windows-msvc-install_only.tar.gz"
$zipPath = Join-Path $outputRoot $zipName

Remove-GeneratedPath -Path $buildRoot -OutputPath $outputRoot
if (Test-Path -LiteralPath $zipPath) {
    Remove-GeneratedPath -Path $zipPath -OutputPath $outputRoot
}
New-Item -ItemType Directory -Force -Path $wheelOutput, $runtimeExtract, $packageCache, $cacheRoot | Out-Null

$gitTop = (& git -C $repoRoot rev-parse --show-toplevel).Trim()
if (-not $gitTop -or -not [System.IO.Path]::GetFullPath($gitTop).Equals($repoFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The current directory is not the expected repository: $repoRoot"
}
$sourceSha = (& git -C $repoRoot rev-parse HEAD).Trim()
$branch = (& git -C $repoRoot branch --show-current).Trim()
$gitStatus = @(& git -C $repoRoot status --porcelain)
$sourceDirty = $gitStatus.Count -gt 0
if ($sourceDirty -and -not $AllowDirty) {
    throw "The repository is dirty. Commit or review changes first, or explicitly use -AllowDirty."
}
if ($sourceDirty) {
    Write-Warning "Building from a dirty repository because -AllowDirty was supplied. The manifest will record source_dirty=true."
}

if (-not (Test-Path -LiteralPath $runtimePinPath) -or -not (Test-Path -LiteralPath $runtimeRequirementsPath)) {
    throw "Portable runtime pin or dependency closure is missing."
}
if (-not (Test-Path -LiteralPath $versionTemplate)) {
    throw "Portable distribution VERSION.txt template is missing."
}
$pin = Get-Content -Raw -LiteralPath $runtimePinPath | ConvertFrom-Json
if ($pin.python_version -ne "3.12.14" -or $pin.architecture -ne "x86_64" -or $pin.distribution_flavor -ne "install_only") {
    throw "The committed runtime pin is not the accepted CPython 3.12.14 Windows x86_64 install-only runtime."
}

if ([string]::IsNullOrWhiteSpace($DeveloperPython)) {
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "A developer Python 3.12 executable is required to build the wheel."
    }
    $DeveloperPython = $pythonCommand.Source
} elseif (Test-Path -LiteralPath $DeveloperPython) {
    $DeveloperPython = (Resolve-Path -LiteralPath $DeveloperPython).Path
} else {
    $pythonCommand = Get-Command $DeveloperPython -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "DeveloperPython was not found: $DeveloperPython"
    }
    $DeveloperPython = $pythonCommand.Source
}
$developerVersion = (& $DeveloperPython --version 2>&1 | Out-String).Trim()
if ($developerVersion -notmatch '^Python 3\.12\.') {
    throw "The developer Python must be Python 3.12.x; found $developerVersion"
}

Write-Host "Building $artifactName"
Write-Host "Repository: $repoRoot"
Write-Host "Branch: $branch"
Write-Host "Source commit: $sourceSha"
Write-Host "Runtime pin: $($pin.release_tag) / $($pin.asset_name)"

& $DeveloperPython -m build --wheel --outdir $wheelOutput $repoRoot
$buildExit = $LASTEXITCODE
if ($buildExit -ne 0) {
    Write-Warning "python -m build failed; retrying with pip wheel for developer environments that lack the build front-end."
    Invoke-Checked -FilePath $DeveloperPython -Arguments @("-m", "pip", "wheel", "--no-deps", "--wheel-dir", $wheelOutput, $repoRoot) -Description "Building the HCM Calculator wheel"
}
$wheelFiles = @(Get-ChildItem -LiteralPath $wheelOutput -Filter "*.whl" -File)
$hcmWheels = @($wheelFiles | Where-Object { $_.Name -match '^hcm_calculator-0\.9\.0-.*\.whl$' })
if ($hcmWheels.Count -ne 1) {
    throw "Expected exactly one HCM Calculator 0.9.0 wheel; found $($hcmWheels.Count)."
}
$hcmWheel = $hcmWheels[0].FullName

$assetUrl = [string]$pin.asset_url
$expectedSha = ([string]$pin.sha256).ToLowerInvariant()
if (-not (Test-Path -LiteralPath $archivePath)) {
    Write-Host "Downloading pinned Astral runtime..."
    Invoke-WebRequest -Uri $assetUrl -OutFile $archivePath
}
$actualSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash.ToLowerInvariant()
if ($actualSha -ne $expectedSha) {
    throw "Pinned runtime SHA-256 mismatch: expected $expectedSha, got $actualSha"
}
Write-Host "Verified runtime SHA-256: $actualSha"

$tarCommand = Get-Command tar.exe -ErrorAction SilentlyContinue
if ($null -eq $tarCommand) {
    throw "Windows tar.exe is required on the developer machine to extract the pinned runtime."
}
Invoke-Checked -FilePath $tarCommand.Source -Arguments @("-xzf", $archivePath, "-C", $runtimeExtract) -Description "Extracting the pinned runtime"
$runtimeSource = Join-Path $runtimeExtract "python"
if (-not (Test-Path -LiteralPath (Join-Path $runtimeSource "python.exe"))) {
    throw "The pinned runtime archive did not contain python/python.exe."
}

$stageRuntime = Join-Path $stageRoot "runtime"
$stageApp = Join-Path $stageRoot "app"
$stageLicenses = Join-Path $stageRoot "licenses"
New-Item -ItemType Directory -Force -Path $stageRuntime, $stageApp, $stageLicenses | Out-Null
Copy-Item -Path "$runtimeSource\*" -Destination $stageRuntime -Recurse -Force
Copy-Item -LiteralPath $launcherTemplate -Destination (Join-Path $stageRoot "Run HCM Calculator.bat") -Force
Copy-Item -LiteralPath $readmeTemplate -Destination (Join-Path $stageRoot "README-TH.txt") -Force
Copy-Item -LiteralPath $versionTemplate -Destination (Join-Path $stageRoot "VERSION.txt") -Force
Copy-Item -LiteralPath (Join-Path $runtimeSource "LICENSE.txt") -Destination (Join-Path $stageLicenses "PYTHON-LICENSE.txt") -Force

$runtimePython = Join-Path $stageRuntime "python.exe"
$runtimeVersion = (& $runtimePython --version 2>&1 | Out-String).Trim()
if ($runtimeVersion -ne "Python 3.12.14") {
    throw "Bundled runtime reported the wrong version: $runtimeVersion"
}

Write-Host "Downloading the pinned normal dependency closure..."
Invoke-Checked -FilePath $runtimePython -Arguments @(
    "-m", "pip", "download", "--disable-pip-version-check", "--no-input", "--no-cache-dir",
    "--only-binary=:all:", "--no-deps", "--dest", $packageCache, "--requirement", $runtimeRequirementsPath
) -Description "Downloading portable runtime dependencies"
Write-Host "Installing only the pinned normal dependency closure..."
Invoke-Checked -FilePath $runtimePython -Arguments @(
    "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-index",
    "--find-links", $packageCache, "--no-compile", "--no-deps", "--target", $stageApp,
    "--requirement", $runtimeRequirementsPath
) -Description "Installing portable runtime dependencies"
Invoke-Checked -FilePath $runtimePython -Arguments @(
    "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-index",
    "--find-links", $wheelOutput, "--no-compile", "--no-deps", "--target", $stageApp,
    "hcm-calculator==0.9.0"
) -Description "Installing the HCM Calculator wheel"
Invoke-Checked -FilePath $runtimePython -Arguments @(
    $pruneScript, "--app-root", $stageApp, "--runtime-root", $stageRuntime
) -Description "Pruning package test payloads"

$runtimeSitePackages = Join-Path $stageRuntime "Lib\site-packages"
if (Test-Path -LiteralPath $runtimeSitePackages) {
    Get-ChildItem -LiteralPath $runtimeSitePackages -Force | Where-Object {
        $_.Name -eq "pip" -or $_.Name -like "pip-*.dist-info"
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
}
$runtimeScripts = Join-Path $stageRuntime "Scripts"
if (Test-Path -LiteralPath $runtimeScripts) {
    Get-ChildItem -LiteralPath $runtimeScripts -Force | Where-Object {
        $_.Name -like "pip*"
    } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
}

$manifestArguments = @(
    $manifestScript, "--root", $stageRoot, "--source-sha", $sourceSha, "--branch", $branch,
    "--runtime-pin", $runtimePinPath, "--requirements", $runtimeRequirementsPath
)
if ($sourceDirty) { $manifestArguments += "--source-dirty" }
Invoke-Checked -FilePath $runtimePython -Arguments $manifestArguments -Description "Generating portable manifests"

Invoke-Checked -FilePath $DeveloperPython -Arguments @(
    $zipScript, "--source-root", $stageRoot, "--output", $zipPath
) -Description "Creating deterministic portable ZIP"

$validationArguments = @($validatorScript, "--root", $stageRoot, "--zip", $zipPath)
if (-not $SkipPortableSmoke) {
    $validationArguments += @("--run-smoke", "--offline", "--no-prerequisites")
} else {
    Write-Warning "Portable runtime smoke was explicitly skipped with -SkipPortableSmoke."
}
Invoke-Checked -FilePath $DeveloperPython -Arguments $validationArguments -Description "Validating portable distribution"

$zipInfo = Get-Item -LiteralPath $zipPath
$zipHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath).Hash.ToLowerInvariant()
Write-Host "Portable distribution build complete."
Write-Host "ZIP: $zipPath"
Write-Host "ZIP size: $($zipInfo.Length) bytes"
Write-Host "ZIP SHA-256: $zipHash"
