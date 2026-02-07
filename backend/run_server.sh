#!/bin/bash
# Script to run the FastAPI server with proper port configuration

# Default port
PORT=${PORT:-8000}
HOST=${HOST:-127.0.0.1}

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port $PORT is already in use!"
    echo ""
    echo "Options:"
    echo "1. Kill the process using port $PORT:"
    echo "   lsof -ti:$PORT | xargs kill -9"
    echo ""
    echo "2. Use a different port:"
    echo "   PORT=8001 ./run_server.sh"
    echo ""
    echo "3. Find what's using the port:"
    echo "   lsof -i :$PORT"
    exit 1
fi

echo "🚀 Starting FastAPI server on http://$HOST:$PORT"
echo "📚 API docs: http://$HOST:$PORT/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --host $HOST --port $PORT --reload

