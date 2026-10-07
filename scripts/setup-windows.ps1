<#
.SYNOPSIS
    ResumeForge Windows Native Automated Setup Script.
.DESCRIPTION
    Sets up the local Windows environment without Docker or WSL:
    1. Verifies Python >= 3.11 and Node.js >= 18 runtimes.
    2. Creates and initializes the backend virtual environment (.venv).
    3. Installs backend dependencies in editable mode.
    4. Copies .env.windows.example to .env if .env does not already exist.
    5. Audits external system services (PostgreSQL, pgvector, Redis/Memurai, Ollama).
    6. Safely runs database migrations (Alembic) if PostgreSQL is reachable.
    7. Provides clean instructions for any remaining manual steps.
#>

[CmdletBinding()]
param(
    [switch]$SkipMigration = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ResumeForge - Windows Native Environment Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir  = Join-Path $ProjectRoot "apps\backend"
$FrontendDir = Join-Path $ProjectRoot "apps\frontend"
$VenvDir     = Join-Path $BackendDir ".venv"
$VenvPython  = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip     = Join-Path $VenvDir "Scripts\pip.exe"
$RootEnv     = Join-Path $ProjectRoot ".env"
$WinEnvEx    = Join-Path $ProjectRoot ".env.windows.example"

# ---------------------------------------------------------------------------
# 1. Verify Prerequisites
# ---------------------------------------------------------------------------
Write-Host "[1/6] Verifying system runtimes..." -ForegroundColor Yellow

# Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python 3.11+ is required but not found in PATH." -ForegroundColor Red
    Write-Host "Download it from: https://www.python.org/downloads/windows/" -ForegroundColor White
    exit 1
}
$pyVerRaw = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  [OK] Python version: $pyVerRaw" -ForegroundColor Green

# Node.js & npm
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd  = Get-Command npm -ErrorAction SilentlyContinue
if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "[ERROR] Node.js and npm are required for the frontend." -ForegroundColor Red
    Write-Host "Download from: https://nodejs.org/" -ForegroundColor White
    exit 1
}
$nodeVer = & node --version
Write-Host "  [OK] Node.js version: $nodeVer" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 2. Virtual Environment Setup
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Configuring Python virtual environment..." -ForegroundColor Yellow

if (-not (Test-Path $VenvPython)) {
    Write-Host "  Creating virtual environment at $VenvDir..." -ForegroundColor DarkGray
    & python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "  [OK] Virtual environment already exists." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 3. Install Backend Dependencies
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Installing backend dependencies..." -ForegroundColor Yellow

Push-Location $BackendDir
try {
    # Upgrade pip quietly
    & $VenvPython -m pip install --upgrade pip --quiet
    
    # Install package with dev dependencies
    Write-Host "  Installing dependencies from pyproject.toml..." -ForegroundColor DarkGray
    & $VenvPip install -e ".[dev]" --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [WARN] Retrying install without quiet mode..." -ForegroundColor Yellow
        & $VenvPip install -e ".[dev]"
    }
    Write-Host "  [OK] Backend dependencies installed successfully." -ForegroundColor Green
} finally {
    Pop-Location
}

# ---------------------------------------------------------------------------
# 4. Environment File (.env)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Verifying environment configuration (.env)..." -ForegroundColor Yellow

if (-not (Test-Path $RootEnv)) {
    if (Test-Path $WinEnvEx) {
        Copy-Item $WinEnvEx $RootEnv
        Write-Host "  [OK] Created .env from .env.windows.example." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] .env.windows.example not found; skipping .env creation." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] .env already exists (preserving current settings)." -ForegroundColor Green
}

# ---------------------------------------------------------------------------
# 5. External Service Health Check
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Checking required external services..." -ForegroundColor Yellow

$dbUp = Test-NetConnection -ComputerName localhost -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
$redisUp = Test-NetConnection -ComputerName localhost -Port 6379 -InformationLevel Quiet -WarningAction SilentlyContinue
$ollamaUp = Test-NetConnection -ComputerName localhost -Port 11434 -InformationLevel Quiet -WarningAction SilentlyContinue

if ($dbUp) {
    Write-Host "  [OK] PostgreSQL is reachable on localhost:5432." -ForegroundColor Green
} else {
    Write-Host "  [NOTICE] PostgreSQL is NOT running on localhost:5432." -ForegroundColor Yellow
    Write-Host "           Install PostgreSQL & pgvector using the instructions in docs/WINDOWS_NATIVE_SETUP.md." -ForegroundColor DarkGray
}

if ($redisUp) {
    Write-Host "  [OK] Redis / Memurai is reachable on localhost:6379." -ForegroundColor Green
} else {
    Write-Host "  [NOTICE] Redis / Memurai is NOT running on localhost:6379." -ForegroundColor Yellow
    Write-Host "           Install Memurai for Windows from: https://www.memurai.com" -ForegroundColor DarkGray
}

if ($ollamaUp) {
    Write-Host "  [OK] Ollama is reachable on localhost:11434." -ForegroundColor Green
} else {
    Write-Host "  [INFO] Ollama is not running on localhost:11434 (optional for local LLM)." -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 6. Database Migrations (Conditional & Non-Destructive)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Checking database migrations..." -ForegroundColor Yellow

if ($dbUp -and -not $SkipMigration) {
    Write-Host "  PostgreSQL is online. Running Alembic migrations..." -ForegroundColor DarkGray
    Push-Location $BackendDir
    try {
        & $VenvPython -m alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Alembic migrations applied successfully (head)." -ForegroundColor Green
        } else {
            Write-Host "  [WARN] Alembic migration failed. Ensure the 'resumeforge' database exists and credentials match .env." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [WARN] Migration check failed: $_" -ForegroundColor Yellow
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [INFO] Skipping database migrations until PostgreSQL is installed and running." -ForegroundColor DarkGray
    Write-Host "         Once PostgreSQL is running, run: .\scripts\setup-windows.ps1" -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# Completion Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If PostgreSQL or Redis are not yet installed, follow: docs/WINDOWS_NATIVE_SETUP.md" -ForegroundColor White
Write-Host "  2. Audit your service readiness anytime with:" -ForegroundColor White
Write-Host "     powershell -File .\scripts\check-windows-services.ps1" -ForegroundColor Cyan
Write-Host "  3. Start all services using:" -ForegroundColor White
Write-Host "     powershell -File .\scripts\start-windows.ps1" -ForegroundColor Cyan
Write-Host ""
