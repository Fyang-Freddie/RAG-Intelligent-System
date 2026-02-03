@echo off
echo ===========================================
echo Setting up Flask virtual environment (Windows)
echo ===========================================

REM Create virtual environment if it doesn't exist
if not exist nlp_venv (
    echo Creating virtual environment...
    python -m venv nlp_venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
call nlp_venv\Scripts\activate

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ===========================================
echo IMPORTANT: Install Tesseract OCR manually
echo ===========================================
echo For image OCR support, download and install Tesseract:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo After installation, add Tesseract to your PATH
echo.
echo Setup complete!
echo To start your app, run:
echo python run.py