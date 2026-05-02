#!/bin/bash
# Setup script for ProteinScout backend dependencies

set -e

echo "=== ProteinScout Backend Setup ==="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    echo "Please install Python 3.11 or later from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Found Python $PYTHON_VERSION"

# Install backend dependencies
echo ""
echo "Installing backend dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r src-tauri/resources/backend/requirements.txt

echo ""
echo "=== Setup Complete ==="
echo "You can now run: npm run tauri dev"
