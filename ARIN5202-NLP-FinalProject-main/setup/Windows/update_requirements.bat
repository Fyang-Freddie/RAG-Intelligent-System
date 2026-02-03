@echo off
echo ===========================================
echo Updating requirements.txt (Windows)
echo ===========================================

cd ..
if exist nlp_venv (
    call nlp_venv\Scripts\activate
) else (
    echo Virtual environment not found. Run setup_env.bat first.
    pause
    exit /b
)

echo Saving current packages to requirements.txt...
pip freeze > requirements.txt

echo requirements.txt updated successfully!
pause
