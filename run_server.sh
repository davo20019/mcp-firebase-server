#!/usr/bin/env bash
set -e # Exit immediately if a command exits with a non-zero status.

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script's directory to ensure relative paths work correctly
cd "$SCRIPT_DIR"

# --- Source .env file if it exists ---
ENV_FILE="$SCRIPT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Sourcing environment variables from $ENV_FILE" >&2
    # Use `set -a` to export all variables defined in .env, and `set +a` to revert
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "No .env file found. Relying on environment variables set by the MCP client." >&2
fi

# --- Sanity Checks ---
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then # Check for common project files
    echo "Error: Missing pyproject.toml or requirements.txt. Are you in the project root?" >&2
    echo "Attempting to run from: $(pwd)" >&2
    # exit 1 # Keep this commented for now to allow more flexibility if run from subdirs by mistake
fi

PYTHON_SCRIPT_PATH="$SCRIPT_DIR/mcp_firebase_server.py"
if [ ! -f "$PYTHON_SCRIPT_PATH" ]; then
    echo "Error: MCP server script not found at $PYTHON_SCRIPT_PATH" >&2
    exit 1
fi

# --- Python Executable Detection ---
PYTHON_EXEC=""

# Define potential virtual environment directories
VENV_PATHS=("$SCRIPT_DIR/.venv" "$SCRIPT_DIR/venv") # Prioritize .venv (uv default)

for venv_path in "${VENV_PATHS[@]}"; do
    if [ -d "$venv_path" ]; then
        echo "Virtual environment directory found at: $venv_path" >&2
        if [ -x "$venv_path/bin/python3" ]; then
            PYTHON_EXEC="$venv_path/bin/python3"
            echo "Using python3 from venv: $PYTHON_EXEC" >&2
            break
        elif [ -x "$venv_path/bin/python" ]; then
            PYTHON_EXEC="$venv_path/bin/python"
            echo "Using python from venv: $PYTHON_EXEC" >&2
            break
        else
            echo "Warning: Found venv at $venv_path, but no python3 or python executable in its bin/ directory." >&2
        fi
    fi
done

# If Python executable not found in any venv, try system PATH
if [ -z "$PYTHON_EXEC" ]; then
    echo "Python not found in .venv or venv, trying system PATH." >&2
    if command -v python3 &>/dev/null; then
        PYTHON_EXEC="python3"
        echo "Using system python3: $(command -v python3)" >&2
    elif command -v python &>/dev/null; then
        PYTHON_EXEC="python"
        echo "Using system python: $(command -v python)" >&2
    fi
fi

# If still no Python executable found, exit
if [ -z "$PYTHON_EXEC" ]; then
    echo "Error: Could not find a suitable python3 or python executable in .venv, venv, or system PATH." >&2
    exit 1
fi

# --- Launch Server ---
echo "Launching MCP Firebase Server using: $PYTHON_EXEC $PYTHON_SCRIPT_PATH" >&2
echo "(SERVICE_ACCOUNT_KEY_PATH and FIREBASE_STORAGE_BUCKET should be set in MCP client's env for this command)" >&2

# Execute the Python MCP server
"$PYTHON_EXEC" "$PYTHON_SCRIPT_PATH" 