@echo off
REM ============================================
REM   STOP MA+RSI Strategy
REM ============================================

echo.
echo ============================================
echo    Stopping MA+RSI Trading Strategy
echo ============================================
echo.

REM Delete the RUNNING flag file
if exist breeze_RUNNING.flag (
    del breeze_RUNNING.flag
    echo [OK] Strategy is now STOPPED
    echo.
    echo The strategy will no longer execute
    echo No signals will be generated
    echo.
) else (
    echo [INFO] Strategy was already stopped
    echo.
)

echo ============================================
echo   Strategy Status: STOPPED
echo.
echo   To START again:
echo   Double-click: START_Strategy.bat
echo ============================================
echo.

pause

