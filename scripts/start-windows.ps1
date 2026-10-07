<#
.SYNOPSIS
    ResumeForge Windows Native Development Server Launcher.
.DESCRIPTION
    Launches or outputs the commands for the 3 local developer services:
    - Terminal 1: FastAPI Backend on http://localhost:8000
    - Terminal 2: Celery Worker with Windows solo pool (-P solo)
    - Terminal 3: Next.js Frontend on http://localhost:3000
.PARAMETER InstructionsOnly
    If specified, prints the exact terminal commands without spawning new windows.
#>

[CmdletBinding()]
param(
    [switch]$InstructionsOnly = $false
)

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir  = Join-Path $ProjectRoot "apps\backend"
$FrontendDir = Join-Path $ProjectRoot "apps\frontend"
$VenvActivate= Join-Path $BackendDir ".venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ResumeForge - Local Development Launcher (Windows Native)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Pre-flight check on external dependencies
$dbUp    = Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
$redisUp = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $dbUp) {
    Write-Host "[WARNING] PostgreSQL (localhost:5432) is not currently reachable." -ForegroundColor Yellow
    Write-Host "          Backend API will report degraded health until PostgreSQL is started." -ForegroundColor DarkGray
}

if (-not $redisUp) {
    Write-Host "[WARNING] Redis / Memurai (localhost:6379) is not currently reachable." -ForegroundColor Yellow
    Write-Host "          Celery worker will wait to connect until Redis/Memurai is started." -ForegroundColor DarkGray
}

if ($InstructionsOnly) {
    Write-Host ""
    Write-Host "Open 3 separate PowerShell terminals and run the following:" -ForegroundColor White
    Write-Host ""
    Write-Host "--- Terminal 1: FastAPI Backend ---" -ForegroundColor Yellow
    Write-Host "cd `"$BackendDir`"" -ForegroundColor Cyan
    Write-Host ".\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "uvicorn app.main:app --reload --port 8000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "--- Terminal 2: Celery Worker (Windows -P solo) ---" -ForegroundColor Yellow
    Write-Host "cd `"$BackendDir`"" -ForegroundColor Cyan
    Write-Host ".\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "celery -A app.workers.celery_app worker --loglevel=info -P solo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "--- Terminal 3: Next.js Frontend ---" -ForegroundColor Yellow
    Write-Host "cd `"$FrontendDir`"" -ForegroundColor Cyan
    Write-Host "npm run dev" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Access Points:" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
    return
}

Write-Host "Launching local developer processes in dedicated terminal windows..." -ForegroundColor Green
Write-Host ""

# 1. Launch FastAPI Backend
$backendScript = @"
Write-Host '=========================================' -ForegroundColor Cyan
Write-Host '  ResumeForge - FastAPI Backend (Port 8000)' -ForegroundColor Cyan
Write-Host '=========================================' -ForegroundColor Cyan
Set-Location '$BackendDir'
& '$VenvActivate'
uvicorn app.main:app --reload --port 8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# 2. Launch Celery Worker (Windows solo pool)
$workerScript = @"
Write-Host '=========================================' -ForegroundColor Cyan
Write-Host '  ResumeForge - Celery Worker (Solo Pool)' -ForegroundColor Cyan
Write-Host '=========================================' -ForegroundColor Cyan
Set-Location '$BackendDir'
& '$VenvActivate'
celery -A app.workers.celery_app worker --loglevel=info -P solo
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerScript

# 3. Launch Next.js Frontend
$frontendScript = @"
Write-Host '=========================================' -ForegroundColor Cyan
Write-Host '  ResumeForge - Next.js Frontend (Port 3000)' -ForegroundColor Cyan
Write-Host '=========================================' -ForegroundColor Cyan
Set-Location '$FrontendDir'
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

Write-Host "All 3 services have been launched in separate terminal windows:" -ForegroundColor Green
Write-Host "  1. Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  2. API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  3. Frontend UI:  http://localhost:3000" -ForegroundColor White
Write-Host ""
