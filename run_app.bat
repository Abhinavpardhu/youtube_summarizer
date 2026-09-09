@echo off

echo ==========================================
echo   YouTube Video Summarizer
echo ==========================================
echo.

cd /d "%~dp0"

echo Checking virtual environment...

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
python -m pip install -r requirements.txt

echo.
echo ==========================================
echo   Starting FastAPI Server
echo ==========================================
echo.

python -m uvicorn main:app --reload

pause