@echo off
REM ============================================
REM   START MA+RSI Strategy
REM ============================================

echo.
echo ============================================
echo    Starting MA+RSI Trading Strategy
echo ============================================
echo.

REM Create the RUNNING flag file
echo RUNNING > breeze_RUNNING.flag

echo [OK] Strategy is now ACTIVE
echo.
echo The strategy will run every 1 minute
echo checking for signals on TATINV and GODPRO
echo.
echo Current mode: Check strategy_config.yaml
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

