# Port Conflict Resolution

If you're getting "Address already in use" errors, here's how to fix it:

## Quick Fix

### Option 1: Kill the process using the port

```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (replace PID with the process ID from above)
kill -9 <PID>

# Or kill directly by port
lsof -ti:8000 | xargs kill -9
```

### Option 2: Use a different port

```bash
# Start server on port 8001
PORT=8001 uvicorn app.main:app --reload --port 8001

# Or use the run script
PORT=8001 ./run_server.sh
```

### Option 3: Use the run script (recommended)

```bash
# Make it executable
chmod +x run_server.sh

# Run it (checks for port conflicts automatically)
./run_server.sh
```

## Check What's Running

```bash
# Check port 8000
lsof -i :8000

# Check port 8001
lsof -i :8001

# Check all Python processes
ps aux | grep python | grep -v grep
```

## Standard Port Configuration

The default port is **8000**. All test scripts will use the same port if you set the `PORT` environment variable:

```bash
# Set port for this session
export PORT=8000

# Or use a different port
export PORT=8001

# Then run server
uvicorn app.main:app --reload --port $PORT
```

## Update Test Scripts

Test scripts automatically use the `PORT` environment variable:

```bash
# Set port
export PORT=8000

# Run test
python test_form_filler.py
```

Or specify inline:

```bash
PORT=8000 python test_form_filler.py
```

