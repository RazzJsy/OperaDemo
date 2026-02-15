#!/bin/bash

echo "Starting Blazor Frontend"

if [ ! -d "OperaDemoWeb/obj" ]; then
    echo ".NET dependencies not found. Restoring..."
    cd OperaDemoWeb
    dotnet restore
    cd ..
fi

echo ""
echo "Starting Blazor Server on http://0.0.0.0:5000"
echo ""
echo "Make sure Python backend is running on port 8000!"
echo "   (Run ./start-backend.sh in another terminal)"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

cd OperaDemoWeb
dotnet run --urls "http://0.0.0.0:5000"
