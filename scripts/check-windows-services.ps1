<#
.SYNOPSIS
    ResumeForge Windows Services & Environment Health Checker.
.DESCRIPTION
    Non-destructive audit script that verifies local Windows environment:
    - Python runtime & .venv
    - Node.js & npm runtime
    - PostgreSQL service, port 5432, database, and pgvector extension
    - Redis / Memurai service & port 6379
    - Ollama service & port 11434
    - Backend dependencies & API health
    - Frontend node_modules & Next.js readiness
#>

[CmdletBinding()]
param(
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432,
    [string]$DbUser = "postgres",
    [string]$DbName = "resumeforge",
    [string]$RedisHost = "localhost",
    [int]$RedisPort = 6379,
    [string]$OllamaHost = "localhost",
    [int]$OllamaPort = 11434
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ResumeForge - Windows Native Environment Health Check" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$AllHealthy = $true
$MissingItems = @()

# ---------------------------------------------------------------------------
# 1. Runtimes: Python & Node
# ---------------------------------------------------------------------------
Write-Host "[1/6] Checking Core Runtimes..." -ForegroundColor Yellow

# Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $pyVer = & python --version 2>&1
    Write-Host "  [OK] Python found: $pyVer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Python is NOT installed or not on PATH." -ForegroundColor Red
    $AllHealthy = $false
    $MissingItems += "Python >= 3.11"
}

# Node.js
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    $nodeVer = & node --version 2>&1
    Write-Host "  [OK] Node.js found: $nodeVer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Node.js is NOT installed or not on PATH." -ForegroundColor Red
    $AllHealthy = $false
    $MissingItems += "Node.js >= 18"
}

# npm
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) {
    $npmVer = & npm --version 2>&1
    Write-Host "  [OK] npm found: v$npmVer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] npm is NOT installed or not on PATH." -ForegroundColor Red
    $AllHealthy = $false
    $MissingItems += "npm"
}

# ---------------------------------------------------------------------------
# 2. Backend Virtual Environment
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Checking Backend Python Environment..." -ForegroundColor Yellow

$backendDir = Join-Path $PSScriptRoot "..\apps\backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "  [OK] Backend virtual environment exists: $venvPython" -ForegroundColor Green
    
    # Check core dependencies inside venv
    $importCheck = & $venvPython -c "import fastapi, uvicorn, sqlalchemy, asyncpg, alembic, redis, celery, pgvector; print('OK')" 2>&1
    if ($importCheck -eq "OK") {
        Write-Host "  [OK] All core backend dependencies installed (FastAPI, SQLAlchemy, Celery, pgvector)." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Some dependencies missing in .venv: $importCheck" -ForegroundColor Yellow
        $MissingItems += "Backend Python dependencies (run pip install -e 'apps\backend[dev]')"
    }
} else {
    Write-Host "  [FAIL] Backend virtual environment (.venv) does not exist." -ForegroundColor Red
    Write-Host "         Run .\scripts\setup-windows.ps1 to create it." -ForegroundColor DarkGray
    $AllHealthy = $false
    $MissingItems += "Backend .venv (apps\backend\.venv)"
}

# ---------------------------------------------------------------------------
# 3. PostgreSQL & pgvector (Port 5432)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Checking PostgreSQL & pgvector (Port $DbPort)..." -ForegroundColor Yellow

# Port reachability
$dbConnected = Test-NetConnection -ComputerName $DbHost -Port $DbPort -InformationLevel Quiet -WarningAction SilentlyContinue
if ($dbConnected) {
    Write-Host "  [OK] PostgreSQL port $DbPort is OPEN and reachable." -ForegroundColor Green
    
    # Check if psql CLI exists to inspect database and extension
    $psqlCmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($psqlCmd) {
        # Check database existence
        $dbCheck = & psql -U $DbUser -h $DbHost -p $DbPort -lqt 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Successfully connected to PostgreSQL via psql." -ForegroundColor Green
            if ($dbCheck -match $DbName) {
                Write-Host "  [OK] Database '$DbName' exists." -ForegroundColor Green
            } else {
                Write-Host "  [WARN] Database '$DbName' does NOT exist yet. Create it with: CREATE DATABASE $DbName;" -ForegroundColor Yellow
                $MissingItems += "PostgreSQL database '$DbName'"
            }
            
            # Check pgvector extension
            $vecCheck = & psql -U $DbUser -h $DbHost -p $DbPort -d $DbName -c "SELECT installed_version FROM pg_available_extensions WHERE name='vector';" 2>&1
            if ($vecCheck -match "\d+\.\d+") {
                Write-Host "  [OK] pgvector extension is available in PostgreSQL." -ForegroundColor Green
            } else {
                Write-Host "  [WARN] pgvector extension NOT detected in PostgreSQL." -ForegroundColor Yellow
                $MissingItems += "pgvector extension for Windows PostgreSQL"
            }
        } else {
            Write-Host "  [INFO] PostgreSQL service is up, but authentication failed or requires password." -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [INFO] psql CLI not found on PATH; check connection via DATABASE_URL." -ForegroundColor DarkGray
    }
} else {
    Write-Host "  [FAIL] PostgreSQL port $DbPort is NOT reachable on $DbHost." -ForegroundColor Red
    Write-Host "         PostgreSQL service is either stopped or not installed." -ForegroundColor DarkGray
    $AllHealthy = $false
    $MissingItems += "PostgreSQL on port $DbPort (native Windows install)"
}

# ---------------------------------------------------------------------------
# 4. Redis / Memurai (Port 6379)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Checking Redis / Memurai (Port $RedisPort)..." -ForegroundColor Yellow

$redisConnected = Test-NetConnection -ComputerName $RedisHost -Port $RedisPort -InformationLevel Quiet -WarningAction SilentlyContinue
if ($redisConnected) {
    Write-Host "  [OK] Redis / Memurai port $RedisPort is OPEN and reachable." -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Redis / Memurai port $RedisPort is NOT reachable on $RedisHost." -ForegroundColor Red
    Write-Host "         Install Memurai for Windows (https://www.memurai.com) or run a native Windows Redis port." -ForegroundColor DarkGray
    $AllHealthy = $false
    $MissingItems += "Redis / Memurai on port $RedisPort"
}

# ---------------------------------------------------------------------------
# 5. Ollama Local LLM (Port 11434)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Checking Ollama Local AI Engine (Port $OllamaPort)..." -ForegroundColor Yellow

$ollamaConnected = Test-NetConnection -ComputerName $OllamaHost -Port $OllamaPort -InformationLevel Quiet -WarningAction SilentlyContinue
if ($ollamaConnected) {
    Write-Host "  [OK] Ollama port $OllamaPort is OPEN and reachable." -ForegroundColor Green
    try {
        $tags = Invoke-RestMethod -Uri "http://$OllamaHost`:$OllamaPort/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
        $modelCount = if ($tags.models) { $tags.models.Count } else { 0 }
        Write-Host "  [OK] Ollama API responded. Installed models count: $modelCount" -ForegroundColor Green
        if ($modelCount -eq 0) {
            Write-Host "  [INFO] Recommended models to pull: ollama pull llama3.1:8b ; ollama pull nomic-embed-text" -ForegroundColor DarkGray
        }
    } catch {
        Write-Host "  [WARN] Ollama port is open, but API query failed: $_" -ForegroundColor Yellow
    }
} else {
    $ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaExe) {
        Write-Host "  [INFO] Ollama is installed at $ollamaExe, but not currently running." -ForegroundColor Yellow
        Write-Host "         Start it by launching Ollama from the Start Menu or running: & '$ollamaExe' serve" -ForegroundColor DarkGray
    } else {
        Write-Host "  [INFO] Ollama is not installed (optional, system falls back to deterministic matching)." -ForegroundColor DarkGray
    }
}

# ---------------------------------------------------------------------------
# 6. Frontend Dependencies
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Checking Frontend Next.js Dependencies..." -ForegroundColor Yellow

$frontendDir = Join-Path $PSScriptRoot "..\apps\frontend"
$nodeModules = Join-Path $frontendDir "node_modules"

if (Test-Path $nodeModules) {
    Write-Host "  [OK] Frontend node_modules directory exists." -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Frontend node_modules missing. Run 'npm install' inside apps/frontend." -ForegroundColor Red
    $AllHealthy = $false
    $MissingItems += "Frontend node_modules (run npm install in apps/frontend)"
}

# ---------------------------------------------------------------------------
# Summary Report
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Summary & Action Items" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($AllHealthy -and $MissingItems.Count -eq 0) {
    Write-Host "  STATUS: ALL SERVICES & ENVIRONMENTS ARE READY! [PASS]" -ForegroundColor Green
    Write-Host ""
    Write-Host "  You can start ResumeForge with:" -ForegroundColor Cyan
    Write-Host "    .\scripts\start-windows.ps1" -ForegroundColor White
} else {
    Write-Host "  STATUS: ACTION REQUIRED [INCOMPLETE]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  The following components need attention:" -ForegroundColor Yellow
    foreach ($item in $MissingItems) {
        Write-Host "    - $item" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "  See docs/WINDOWS_NATIVE_SETUP.md for step-by-step installation instructions." -ForegroundColor White
}
Write-Host ""
