@echo off
REM ============================================
REM   STATUS Check for MA+RSI Strategy
REM ============================================

echo.
echo ============================================
echo    MA+RSI Strategy Status
echo ============================================
echo.

REM Check if strategy is running
if exist breeze_RUNNING.flag (
    echo Strategy Status: RUNNING [OK]
    echo.
    
    REM Show last run info if available
    if exist logs\last_run.txt (
        echo Last Execution:
        echo ----------------
        type logs\last_run.txt
        echo.
    )
    
    REM Show current positions if available
    if exist logs\positions.txt (
        echo.
        echo Current Positions:
        echo ==================
        type logs\positions.txt
        echo.
    )
    
    echo ============================================
    echo To STOP: Double-click STOP_Strategy.bat
    echo ============================================
    
) else (
    echo Strategy Status: STOPPED [X]
    echo.
    echo The strategy is currently inactive
    echo No signals are being generated
    echo.
    echo ============================================
    echo To START: Double-click START_Strategy.bat
    echo ============================================
)

echo.
pause

