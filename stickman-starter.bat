@echo off
setlocal

rem Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found. Please install Python 3.x from https://www.python.org/downloads/
    echo Then run this script again.
    pause
    exit /b 1
)

rem Check Python version (optional, but good practice)
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PYTHON_MAJOR_VERSION=%%i
if "%PYTHON_MAJOR_VERSION%" neq "3" (
    echo This script requires Python 3.x. Your current Python version might be older.
    echo Please ensure Python 3 is in your PATH.
    pause
    exit /b 1
)

rem Check if pip is installed
where pip >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not found. It usually comes with Python 3.x.
    echo Please ensure pip is installed and in your PATH.
    pause
    exit /b 1
)

rem Check if virtual environment exists, if not, create it
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

:: ========================================================================
:: MODIFIED SECTION
:: This step now upgrades pip AND installs the build tools (setuptools/wheel)
:: that pygame needs to compile. This fixes the 'distutils' error.

rem Upgrade pip and install essential build tools
echo Upgrading pip, setuptools, and wheel...
python.exe -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo Failed to upgrade pip or install build tools.
    pause
    exit /b 1
)
:: ========================================================================

rem Install dependencies
echo Installing/updating dependencies from requirements.txt...
pip install --no-build-isolation -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

rem Run the main application
echo Starting the Stickman game...
python stickman_fighter.py

rem Deactivate virtual environment (optional, but good practice)
echo Deactivating virtual environment...
call venv\Scripts\deactivate.bat

echo Script finished.
pause
endlocal