#!/bin/bash
echo "==========================================="
echo "Updating requirements.txt (Mac/Linux)"
echo "==========================================="

cd "$(dirname "$0")/../.."

if [ -d "nlp_venv" ]; then
    source nlp_venv/bin/activate
else
    echo "Virtual environment not found. Run setup_env.sh first."
    exit 1
fi

echo "Saving current packages to requirements.txt..."
pip freeze > requirements.txt

echo "requirements.txt updated successfully!"
