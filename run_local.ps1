# Loads .env into this process and runs hostel_check.py with any args passed through.
# Usage:  .\run_local.ps1 --dry-run
$ErrorActionPreference = "Stop"

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    throw "No .env found. Copy .env.example to .env and fill it in."
}

Get-Content $envFile | Where-Object { $_ -match "^\s*[^#\s].*=" } | ForEach-Object {
    $pair = $_ -split "=", 2
    [Environment]::SetEnvironmentVariable($pair[0].Trim(), $pair[1].Trim(), "Process")
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $python (Join-Path $PSScriptRoot "hostel_check.py") @args
