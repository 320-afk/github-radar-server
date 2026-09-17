#!/bin/bash
# Start the GitHub Radar Server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]" -q

# Start server
echo "Starting GitHub Radar Server on http://0.0.0.0:8080"
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
