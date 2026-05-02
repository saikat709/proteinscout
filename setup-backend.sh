#!/bin/bash
# Setup script for ProteinScout backend dependencies

set -e

echo "=== ProteinScout Backend Setup ==="
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Unknown"
fi

echo "Detected OS: $OS"
echo ""

# macOS-specific setup
if [ "$OS" = "macOS" ]; then
    echo "macOS Setup Instructions:"
    echo "1. Install Xcode Command Line Tools (if not already installed):"
    echo "   xcode-select --install"
    echo ""
    echo "2. Install build tools via Homebrew:"
    echo "   brew install make gcc"
    echo ""
    echo "3. (Optional) Install HMMER via Homebrew:"
    echo "   brew tap brewsci/bio && brew install hmmer"
    echo ""
    echo "Note: The app can automatically download and compile HMMER"
    echo "on first run if not installed."
    echo ""
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required but not installed."
    if [ "$OS" = "macOS" ]; then
        echo "Install via Homebrew: brew install python@3.11"
    else
        echo "Please install Python 3.11 or later from https://www.python.org/"
    fi
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
if [ "$OS" = "macOS" ]; then
    echo "Next: npm run tauri:dev (to test the app)"
    echo "Or: npm run tauri:build (to create a .dmg for distribution)"
else
    echo "Next: npm run tauri:dev (to test the app)"
fi

