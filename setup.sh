#!/bin/bash

# Setup script for the MCP Firebase Server

set -e # Exit immediately if a command exits with a non-zero status.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" # Ensure we are in the script's directory

PYPROJECT_FILE="pyproject.toml"
REQUIREMENTS_FILE="requirements.txt"
RUN_SERVER_SCRIPT="run_server.sh"
ENV_FILE=".env"
VENV_DIR=".venv" # uv default

echo "Starting MCP Firebase Server setup (running from $(pwd))..."

# 1. Check if required project files exist (basic sanity check)
if [ ! -f "$REQUIREMENTS_FILE" ] && [ ! -f "$PYPROJECT_FILE" ]; then
    echo "Error: Missing $REQUIREMENTS_FILE or $PYPROJECT_FILE." >&2
    echo "Please ensure you are running this script from within the project root directory." >&2
    exit 1
fi
if [ ! -f "$RUN_SERVER_SCRIPT" ]; then
    echo "Error: Missing $RUN_SERVER_SCRIPT. This script should be present to make executable." >&2
    exit 1
fi
echo "Project files found."

# 2. Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' command not found." >&2
    echo "Please install uv first. See: https://github.com/astral-sh/uv" >&2
    exit 1
fi
echo "'uv' command found."

# 3. Create virtual environment using uv
echo "Creating Python virtual environment in '$VENV_DIR' using 'uv venv' (if it doesn't exist)..." >&2
if [ ! -d "$VENV_DIR" ]; then
    uv venv
    echo "Virtual environment created." >&2
else
    echo "Virtual environment '$VENV_DIR' already exists. Skipping creation." >&2
fi

# Ensure the venv python exists before proceeding
VENV_PYTHON_EXEC="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PYTHON_EXEC" ]; then
    # Try python3 if python is not found (less common for venvs but good to check)
    VENV_PYTHON_EXEC="$VENV_DIR/bin/python3"
    if [ ! -x "$VENV_PYTHON_EXEC" ]; then
        echo "Error: Virtual environment Python executable not found at $VENV_DIR/bin/python or $VENV_DIR/bin/python3 after 'uv venv'." >&2
        exit 1
    fi
fi
echo "Virtual environment Python executable found at $VENV_PYTHON_EXEC." >&2

# 4. Install dependencies using uv
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE using 'uv pip install' (this might take a moment)..." >&2
    uv pip install -r "$REQUIREMENTS_FILE"
else
    echo "Warning: $REQUIREMENTS_FILE not found. Cannot install dependencies." >&2
fi

# 5. Configure .env file
echo "
Configuring Firebase credentials..."

read -p "Enter the ABSOLUTE path to your Firebase service account JSON file: " SERVICE_ACCOUNT_KEY_PATH_INPUT
while [ -z "$SERVICE_ACCOUNT_KEY_PATH_INPUT" ]; do
    read -p "Path cannot be empty. Please enter the ABSOLUTE path to your Firebase service account JSON file: " SERVICE_ACCOUNT_KEY_PATH_INPUT
done

# Basic check if the provided path exists (optional, but helpful)
if [ ! -f "$SERVICE_ACCOUNT_KEY_PATH_INPUT" ]; then
    echo "Warning: The provided service account key path does not seem to exist: $SERVICE_ACCOUNT_KEY_PATH_INPUT" >&2
    echo "Please double-check the path. The .env file will be created with the provided path anyway." >&2
fi

read -p "Enter your Firebase Storage bucket name (e.g., your-project-id.appspot.com): " FIREBASE_STORAGE_BUCKET_INPUT
while [ -z "$FIREBASE_STORAGE_BUCKET_INPUT" ]; do
    read -p "Bucket name cannot be empty. Please enter your Firebase Storage bucket name: " FIREBASE_STORAGE_BUCKET_INPUT
done

# Create or overwrite .env file
echo "Creating/updating $ENV_FILE file..." >&2
{
    echo "# Firebase Configuration for MCP Server"
    echo "SERVICE_ACCOUNT_KEY_PATH=\"$SERVICE_ACCOUNT_KEY_PATH_INPUT\""
    echo "FIREBASE_STORAGE_BUCKET=\"$FIREBASE_STORAGE_BUCKET_INPUT\""
} > "$ENV_FILE"
echo "$ENV_FILE created/updated successfully." >&2

# 6. Make run_server.sh executable
echo "Making $RUN_SERVER_SCRIPT executable..." >&2
chmod +x "$RUN_SERVER_SCRIPT"
echo "$RUN_SERVER_SCRIPT is now executable." >&2

# 7. Print final instructions
echo "
Setup script finished.

Next Steps:
1. Ensure your MCP client (e.g., Claude Desktop) is configured to run the server using the command:
   $SCRIPT_DIR/$RUN_SERVER_SCRIPT
   (Remember to use the absolute path in the client configuration).

2. The server will now use the credentials configured in $SCRIPT_DIR/$ENV_FILE.
   If you need to change them, you can edit the $ENV_FILE directly or re-run this setup script.

3. You can test the server locally by running:
   $SCRIPT_DIR/$RUN_SERVER_SCRIPT
   Or with the MCP Inspector (if you have 'mcp' CLI tools installed globally or in a parent venv):
   mcp dev $SCRIPT_DIR/mcp_firebase_server.py
" >&2 