#!/bin/bash

# QBR Automation - Development Startup Script
# Starts both API and Frontend servers

echo "======================================"
echo "QBR Automation - Starting Dev Servers"
echo "======================================"
echo ""

# Kill any existing processes on ports 8000 and 5173
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
sleep 2

# Start API server in background
echo "Starting API server on http://localhost:8000..."
cd "$(dirname "$0")"
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"
echo "API logs: tail -f api.log"
sleep 3

# Check if API started
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ API server running at http://localhost:8000"
    echo "   Swagger docs at http://localhost:8000/docs"
else
    echo "❌ API server failed to start. Check api.log"
    exit 1
fi

# Start frontend
echo ""
echo "Starting frontend on http://localhost:5173..."
echo "Press CTRL+C to stop both servers"
echo ""
cd frontend

# Trap CTRL+C to kill both processes
trap "echo ''; echo 'Stopping servers...'; kill $API_PID 2>/dev/null; lsof -ti:8000 | xargs kill -9 2>/dev/null; lsof -ti:5173 | xargs kill -9 2>/dev/null; echo 'Servers stopped.'; exit 0" INT TERM

# Start frontend (this blocks)
npm run dev

# If npm exits, clean up API
kill $API_PID 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
