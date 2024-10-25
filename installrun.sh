#!/bin/bash

REPO_URL="https://github.com/The10axe/The10botRevival.git"
REPO_DIR="The10botRevival"

# Check if the repository directory exists
if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    git fetch

    # Check if there are updates
    if [ $(git rev-parse HEAD) != $(git rev-parse @{u}) ]; then
        git pull
    fi
else
    # Clone the repository if it doesn't exist
    git clone "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"

fi

# Run the main.py script
python3 -m venv bot-env
source bot-env/bin/activate
pip install -r requirements.txt
python3 main.py
