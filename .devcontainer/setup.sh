#!/bin/bash

echo "Setting up OperaDemo"

echo "Installing system build tools..."
sudo apt-get update && sudo apt-get install -y build-essential

echo ""
echo "Installing Python dependencies..."
pip install --no-cache-dir --break-system-packages torch --index-url https://download.pytorch.org/whl/cpu
pip install --no-cache-dir --break-system-packages -r requirements.txt

echo ""
echo "Restoring .NET dependencies..."
cd OperaDemoWeb
dotnet restore
cd ..

chmod +x start.sh
chmod +x start-backend.sh
chmod +x start-frontend.sh

echo ""
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "  ./start.sh          (starts both backend and frontend)"
echo ""
echo "Or start individually:"
echo "  ./start-backend.sh  (Python API on port 8000)"
echo "  ./start-frontend.sh (Blazor UI on port 5000)"
echo ""