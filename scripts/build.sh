#!/bin/bash
# E.M.B.E.R Build Script

cd "$(dirname "$0")"

echo "Building E.M.B.E.R..."

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Installing dependencies..."
pip install -r requirements.txt 2>/dev/null || true

echo "Building complete!"
