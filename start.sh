#!/bin/bash

echo "Starting OperaDemo"

cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

echo ""
echo "Starting Python API backend (port 8000)..."
python main.py > backend.log 2>&1 &
BACKEND_PID=$!

echo "   Waiting for backend to initialize..."
sleep 5

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend failed to start. Check backend.log for details."
    exit 1
fi

echo "   Backend ready"

echo ""
echo "Starting Blazor frontend (port 5000)..."
cd OperaDemoWeb
dotnet run --urls "http://0.0.0.0:5000" > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "   Waiting for frontend to initialize..."
sleep 8

if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Frontend failed to start. Check frontend.log for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "   Frontend ready"

echo ""
echo "Application is running!"
echo ""
echo "Access the application:"
echo "   Blazor UI:  http://localhost:5000"
echo "   Python API: http://localhost:8000"
echo "   API Docs:   http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

wait $BACKEND_PID $FRONTEND_PID
