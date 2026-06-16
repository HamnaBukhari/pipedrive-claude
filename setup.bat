@echo off
setlocal EnableDelayedExpansion
title Pipedrive MCP Setup

echo.
echo ============================================
echo   Pipedrive MCP Server - Setup
echo ============================================
echo.

REM ── Step 1: Check Python ─────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo [OK] Python found.

REM ── Step 2: Install uv ───────────────────────
uv --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing uv package manager...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    uv --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install uv. Please install it manually:
        echo   https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    echo [OK] uv installed.
) else (
    echo [OK] uv found.
)

REM ── Step 3: Install Python dependencies ──────
echo [INFO] Installing dependencies...
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"
uv pip install "mcp[cli]" httpx python-dotenv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

REM ── Step 4: Ask for API token ─────────────────
echo.
echo ============================================
echo   Enter your Pipedrive API Token
echo ============================================
echo.
echo To find your token:
echo   1. Log in to Pipedrive
echo   2. Click your avatar (top right)
echo   3. Go to Personal preferences ^> API
echo   4. Copy your personal API token
echo.
set /p "API_TOKEN=Paste your token here and press Enter: "

if "!API_TOKEN!"=="" (
    echo [ERROR] No token entered. Setup cancelled.
    pause
    exit /b 1
)

REM ── Step 5: Write .env ────────────────────────
echo PIPEDRIVE_API_TOKEN=!API_TOKEN!> "%SCRIPT_DIR%\.env"
echo [OK] .env file created.

REM ── Step 6: Write .mcp.json ──────────────────
set "PARENT_DIR=%SCRIPT_DIR%\.."
pushd "%PARENT_DIR%"
set "PARENT_DIR=%CD%"
popd

set "PYTHON_PATH=%SCRIPT_DIR%\.venv\Scripts\python.exe"
set "SERVER_PATH=%SCRIPT_DIR%\server.py"

REM Escape backslashes for JSON
set "PYTHON_PATH_JSON=%PYTHON_PATH:\=\\%"
set "SERVER_PATH_JSON=%SERVER_PATH:\=\\%"
set "SCRIPT_DIR_JSON=%SCRIPT_DIR:\=\\%"

(
echo {
echo   "mcpServers": {
echo     "pipedrive": {
echo       "command": "%PYTHON_PATH_JSON%",
echo       "args": ["-u", "%SERVER_PATH_JSON%"],
echo       "cwd": "%SCRIPT_DIR_JSON%",
echo       "env": {
echo         "PIPEDRIVE_API_TOKEN": "!API_TOKEN!",
echo         "PYTHONUNBUFFERED": "1"
echo       }
echo     }
echo   }
echo }
) > "%PARENT_DIR%\.mcp.json"
echo [OK] .mcp.json created.

REM ── Step 7: Update Claude Code settings ──────
set "CLAUDE_SETTINGS=%USERPROFILE%\.claude\settings.json"
if exist "%CLAUDE_SETTINGS%" (
    powershell -Command "$s = Get-Content '%CLAUDE_SETTINGS%' -Raw | ConvertFrom-Json; if (-not $s.enabledMcpjsonServers) { $s | Add-Member -MemberType NoteProperty -Name 'enabledMcpjsonServers' -Value @('pipedrive') } elseif ($s.enabledMcpjsonServers -notcontains 'pipedrive') { $s.enabledMcpjsonServers += 'pipedrive' }; $s | ConvertTo-Json -Depth 10 | Set-Content '%CLAUDE_SETTINGS%'" >nul 2>&1
    echo [OK] Claude Code settings updated.
)

REM ── Done ──────────────────────────────────────
echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Open your project folder in VS Code
echo   2. Reload the window: Ctrl+Shift+P -^> "Developer: Reload Window"
echo   3. The Pipedrive MCP server will connect automatically
echo   4. Try asking Claude: "Show me all open deals"
echo.
pause
