@echo off
REM ============================================
REM   Internal wrapper for Task Scheduler
REM   DO NOT RUN THIS MANUALLY
REM   Use START_Strategy.bat instead
REM ============================================

cd /d "%~dp0"
python scripts\examples\ma_rsi_strategy.py

