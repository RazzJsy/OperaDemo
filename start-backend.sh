#!/bin/bash

echo "Starting Python API Backend"

if ! python -c "import fastapi" 2>/dev/null; then
    echo "Python dependencies not found. Installing..."
    pip install --break-system-packages -r requirements.txt
fi

echo ""
echo "Starting FastAPI server on http://0.0.0.0:8000"
echo ""
echo "Sample documents will be auto-loaded"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py