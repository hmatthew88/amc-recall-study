#!/bin/bash

# Configuration
PROJECT_DIR="/Users/matthewwang/MyDocuments/Antigravity/telegram scratch"
VENV_DIR="$PROJECT_DIR/.venv"
MAIN_SCRIPT="$PROJECT_DIR/automated_update.py"

echo "=== Starting Weekly Update Execution ==="
date

# Navigate to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Set GEMINI and DEEPSEEK keys if they are not already in environment
# Note: Load from .env just in case subprocess doesn't catch them
# But the python script already has load_dotenv()

# Run the automation script
if python3 "$MAIN_SCRIPT"; then
    echo "=== Weekly Update Execution Finished Successfully ==="
    
    # --- Deploy to GitHub Pages ---
    echo "Deploying to GitHub Pages..."
    # Get token from .env
    GITHUB_TOKEN=$(grep GITHUB_TOKEN "$PROJECT_DIR"/.env | cut -d'=' -f2)
    
    cp "$PROJECT_DIR/AMC_Study_App.html" "$PROJECT_DIR/index.html"
    
    # Configure git and push
    git config user.name "hmatthew88"
    git config user.email "wmatt.doc@gmail.com"
    git add AMC_Study_App.html index.html downloads/
    git commit -m "Weekly update: $(date)"
    
    # Push using Token for authentication
    git push --force "https://hmatthew88:${GITHUB_TOKEN}@github.com/hmatthew88/amc-recall-study.git" main
    
    osascript -e 'display notification "AMC Study App has been updated and pushed to GitHub Pages" with title "AMC Weekly Update Success"'
else
    echo "=== Weekly Update Execution Failed ==="
    osascript -e 'display notification "Wait, something went wrong with the weekly update. Check update_log.txt." with title "AMC Weekly Update Failed"'
    exit 1
fi

date
