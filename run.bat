@echo off
REM Weather Data Processor
REM Usage: run.bat data\weather_march.csv

if "%~1"=="" (
    echo Usage: run.bat data\weather_march.csv
    exit /b 1
)

REM Check Python is installed before trying to use it
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Please install Python 3.
    exit /b 1
)

if not exist "%~1" (
    echo Cannot find %~1
    exit /b 1
)

python weather_processor.py "%~1"
if errorlevel 1 (
    echo The program stopped because of an error.
    exit /b 1
)

echo.
REM %~n1 is the input file name without .csv
type "results\%~n1_summary.txt"
