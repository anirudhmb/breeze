@echo off
REM ============================================
REM   SETUP Task Scheduler for MA+RSI Strategy
REM   Run this ONCE to set up automatic execution
REM ============================================

echo.
echo ============================================
echo    Task Scheduler Setup
echo ============================================
echo.

REM Get current directory
set SCRIPT_DIR=%~dp0
set WRAPPER_SCRIPT=%SCRIPT_DIR%RUN_Strategy_Silent.vbs

echo This will create a Windows Task Scheduler job that:
echo   - Runs every 1 minute
echo   - Starts at 9:00 AM daily
echo   - Runs SILENTLY (no flashing windows)
echo.
echo Wrapper script: %WRAPPER_SCRIPT%
echo.

REM Check if python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and in your PATH
    echo.
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Delete existing task if it exists
schtasks /Query /TN "BreezeStrategy" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Removing existing task...
    schtasks /Delete /TN "BreezeStrategy" /F >nul 2>&1
)

echo.
echo Creating Task Scheduler job...
echo.

REM Create the scheduled task
REM Using VBScript wrapper to run silently without flashing windows
schtasks /Create /TN "BreezeStrategy" /TR "wscript.exe \"%WRAPPER_SCRIPT%\"" /SC MINUTE /MO 1 /ST 09:00 /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   SUCCESS! Task Scheduler is configured
    echo ============================================
    echo.
    echo Task Name: BreezeStrategy
    echo Frequency: Every 1 minute
    echo Start Time: 9:00 AM daily
    echo Mode: SILENT (no flashing windows)
    echo.
    echo IMPORTANT NOTES:
    echo 1. The task is created but strategy is NOT running yet
    echo 2. You must run START_Strategy.bat to enable it
    echo 3. The task runs silently every minute checking for the flag
    echo 4. NO MORE FLASHING WINDOWS!
    echo 5. Use STOP_Strategy.bat to disable
    echo.
    echo ============================================
    echo   Next Step: Double-click START_Strategy.bat
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   ERROR: Failed to create task
    echo ============================================
    echo.
    echo You may need to:
    echo 1. Run this batch file as Administrator
    echo 2. Check if Task Scheduler service is running
    echo.
)

echo.
pause

