# Virtual Environment
## Setup Instructions

All setup scripts are inside the `setup/` folder.

### Windows
```bash
setup\Windows\setup_env.bat
```

### Mac/Linux
```bash
chmod +x setup/Unix/setup_env.sh (only needs to be ran once)
source ./setup/Unix/setup_env.sh
```
### Update Requirements

After installing new packages in your virtual environment, run:

#### Windows
```bash
setup\Windows\update_requirements.bat
```
#### Mac/Linux
```bash
chmod +x setup/Unix/update_requirements.sh (only needs to be ran once)
./setup/Unix/update_requirements.sh
```

## Individual Commands
### Create Virtual Environment 
```bash
python3.12 -m venv nlp_venv
```

### Activate Virtual Environment 
#### Windows
```bash
nlp_venv\Scripts\activate
```
#### MacOS/Linux
```bash
source nlp_venv/bin/activate
```

### Libraries/Packages
#### Generating/Updating `requirements.txt`
```bash
pip freeze > requirements.txt
```
#### Installing from `requirements.txt`
```bash
pip install -r requirements.txt
```


# Ollama Setup (Required for Vision AI)

This project uses [Ollama](https://ollama.ai/) to run the MiniCPM-V vision model locally for image understanding.

## Install Ollama

### Windows
1. Download the Windows installer from [ollama.ai/download](https://ollama.ai/download)
2. Run the installer (`OllamaSetup.exe`)
3. Ollama will start automatically as a service
4. Verify installation: Open Command Prompt and run `ollama --version`

### macOS
```bash
# Using Homebrew
brew install ollama

# Start Ollama
brew services start ollama
```

### Linux
```bash
# Install Ollama (recommended for full GPU support)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve
```

**Note**: If you installed Ollama via snap (`snap install ollama`), it may not have proper GPU access. For best performance with NVIDIA GPUs, use the official installer above and remove the snap version first with `sudo snap remove ollama`.

## Pull the MiniCPM-V Model

After installing Ollama, download the MiniCPM-V vision model:

```bash
ollama pull minicpm-v
```

This will download the MiniCPM-V model (~4GB). The model is optimized for:
- OCR and text recognition
- Asian language support
- Landmark and object identification
- Image description generation

## Verify Ollama Setup

Test that Ollama is working:

```bash
# Check if Ollama is running
ollama list
```

**Note**: The Ollama service must be running for image processing features to work. On Windows and macOS, it runs automatically in the background. On Linux, you may need to start it manually with `ollama serve`.

# Environment Variables

Create a `.env` file in the project root directory with the following API keys (`.env.example` provided):

```env
# Required
HKGAI_API_KEY=your_hkgai_api_key_here

GOOGLE_SEARCH_API_KEY=your_serpapi_key_here
OPENWEATHER_API_KEY=your_openweather_key_here
GOLD_API_KEY=your_gold_api_key_here

# Flask Configuration
FLASK_ENV=development
```

**Note**: API keys are provided already in the project submission for the course.

# Running the App
## Run the Web App
```bash
python run.py
```

## Run Test Script
This script contains provided sample queries to test the pipeline functionality:
```bash
python test_quick.py
```