Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Virtual environment is missing: $PythonExe. Create it with: python -m venv .venv"
}

$Arguments = @("scripts/run_and_open_report.py") + $args

Push-Location $RootDir
try {
    & $PythonExe @Arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
