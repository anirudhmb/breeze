@echo off
REM ============================================
REM   START MA+RSI Strategy
REM ============================================

echo.
echo ============================================
echo    Starting MA+RSI Trading Strategy
echo ============================================
echo.

REM Check if Task Scheduler is set up
schtasks /Query /TN "BreezeStrategy" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Task Scheduler not found!
    echo.
    echo The task "BreezeStrategy" does not exist.
    echo Please run SETUP_TaskScheduler.bat first.
    echo.
    pause
    exit /b 1
)

REM Create the RUNNING flag file
echo RUNNING > breeze_RUNNING.flag

echo [OK] Flag file created
echo.
echo Running strategy once now to test...
echo.

REM Run the strategy once immediately
cd /d "%~dp0"
python scripts\examples\ma_rsi_strategy.py

echo.
echo ============================================
echo   Strategy is now ACTIVE
echo ============================================
echo.
echo The strategy will run automatically every 1 minute
echo via Windows Task Scheduler.
echo.
echo Stocks: TATINV, GODPRO
echo Mode: Check strategy_config.yaml
echo.
echo ============================================
echo   To STOP the strategy:
echo   Double-click: STOP_Strategy.bat
echo.
echo   To CHECK status:
echo   Double-click: STATUS_Strategy.bat
echo ============================================
echo.

pause

