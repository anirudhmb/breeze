@echo off
REM ============================================
REM   Internal wrapper for Task Scheduler
REM   DO NOT RUN THIS MANUALLY
REM   Use START_Strategy.bat instead
REM ============================================

cd /d "%~dp0"

REM Check if the RUNNING flag file exists
if not exist "breeze_RUNNING.flag" (
    REM Strategy is not started, do nothing
    exit /b 0
)

REM Flag exists, activate venv and run the strategy
call venv\Scripts\activate.bat
python scripts\examples\ma_rsi_strategy.py

