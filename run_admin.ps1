# Activates the project's virtualenv and runs the Admin UI
# Usage: Open PowerShell in the repository and run: .\run_admin.ps1

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

# Activate venv if present
$venv = Join-Path $root '.venv\Scripts\Activate.ps1'
if (Test-Path $venv) {
    Write-Host "Activating virtualenv..."
    . $venv
} else {
    Write-Host "No .venv found, continuing with system Python"
}

Write-Host "Starting Admin UI..."
python .\admin\admin_panel_ui\main.py
