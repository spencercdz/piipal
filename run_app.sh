#!/bin/bash

# PII Blurring Tool - Startup Script
echo "🚀 Starting PII Blurring Tool..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    exit 1
fi

# Activate conda environment
echo "📦 Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate env

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate conda environment 'env'"
    echo "Please make sure the environment exists: conda create -n env python=3.8"
    exit 1
fi

echo "✅ Conda environment activated"

# Check if required Python packages are installed
echo "🔍 Checking Python dependencies..."
python -c "import fastapi, uvicorn, easyocr, cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    pip install fastapi uvicorn python-multipart
fi

# Check if Node.js dependencies are installed
echo "🔍 Checking Node.js dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend server
echo "🔧 Starting backend server..."
cd backend
python server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000 > /dev/null; then
    echo "❌ Error: Backend server failed to start"
    exit 1
fi

echo "✅ Backend server running on http://localhost:8000"

# Start frontend server
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Check if frontend is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "⚠️  Frontend might be running on a different port (check terminal output)"
fi

echo "✅ Frontend server starting on http://localhost:3000"
echo ""
echo "🌐 PII Blurring Tool is now running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user to stop the script
wait
