#!/bin/bash
echo "==========================================="
echo "Setting up Flask virtual environment (Mac/Linux)"
echo "==========================================="

# Create virtual environment if it doesn't exist
if [ ! -d "nlp_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv nlp_venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source nlp_venv/bin/activate

# Install system dependencies
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    echo "Detected apt-get (Debian/Ubuntu)"
    sudo apt-get install -y tesseract-ocr
elif command -v brew &> /dev/null; then
    echo "Detected Homebrew (macOS)"
    brew install tesseract
else
    echo "Warning: Could not detect package manager. Please install tesseract-ocr manually."
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo
echo "Setup complete!"
echo "To start your app, run:"
echo "python3 run.py"