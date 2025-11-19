@echo off
echo ========================================
echo Anchormotors ACC Fleet Test
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

echo Installing required packages...
pip install -r requirements.txt

echo.
echo Running fleet test...
python fleet_test.py

echo.
echo ========================================
echo Fleet test completed!
echo Check the results/ folder for plots
echo ========================================
pause
