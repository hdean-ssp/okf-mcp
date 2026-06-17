#!/usr/bin/env bash
# activate.sh — detect best Python, create venv if needed, activate and install.
# Usage: source activate.sh

set -e

MIN_MAJOR=3
MIN_MINOR=10

# --- Find best available Python (highest version >= 3.10) ---

best_python=""
best_minor=0

for minor in 13 12 11 10; do
    for candidate in "python3.${minor}" "python${MIN_MAJOR}.${minor}"; do
        if command -v "$candidate" &>/dev/null; then
            best_python="$candidate"
            best_minor=$minor
            break 2
        fi
    done
done

# Fallback: check if plain python3 meets the minimum
if [ -z "$best_python" ]; then
    if command -v python3 &>/dev/null; then
        py_minor=$(python3 -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
        if [ "$py_minor" -ge "$MIN_MINOR" ] 2>/dev/null; then
            best_python="python3"
            best_minor=$py_minor
        fi
    fi
fi

if [ -z "$best_python" ]; then
    echo "error: No Python >= ${MIN_MAJOR}.${MIN_MINOR} found on PATH."
    echo "Install Python 3.10+ and try again (e.g. sudo apt install python3.12 python3.12-venv)"
    return 1 2>/dev/null || exit 1
fi

echo "Using $best_python (3.${best_minor})"

# --- Create venv if it doesn't exist or was built with wrong Python ---

VENV_DIR=".venv"
rebuild=false

if [ -d "$VENV_DIR" ]; then
    # Check the Python version inside the existing venv
    venv_minor=$("$VENV_DIR/bin/python" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
    if [ "$venv_minor" -lt "$MIN_MINOR" ]; then
        echo "Existing venv uses Python 3.${venv_minor} (too old). Rebuilding..."
        rm -rf "$VENV_DIR"
        rebuild=true
    fi
else
    rebuild=true
fi

if [ "$rebuild" = true ]; then
    echo "Creating venv with $best_python..."
    "$best_python" -m venv "$VENV_DIR"
fi

# --- Activate ---

source "$VENV_DIR/bin/activate"

# --- Install if needed ---

if [ "$rebuild" = true ] || ! pip show okf-mcp &>/dev/null; then
    echo "Installing okf-mcp..."
    pip install --upgrade pip -q
    pip install -e . -q
    echo "Done. 'okf' and 'okf-mcp' commands are now available."
else
    echo "venv active. okf-mcp already installed."
fi
