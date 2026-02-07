# Testing the Screen Control API

Here are several easy ways to test the Screen Control API locally:

## Method 1: FastAPI Automatic Docs (Easiest! ⭐)

The **easiest way** is to use FastAPI's built-in interactive documentation:

1. **Start the server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Open your browser:**
   - Swagger UI (interactive): http://localhost:8000/docs
   - ReDoc (documentation): http://localhost:8000/redoc

3. **Test endpoints:**
   - Click on any endpoint (e.g., `GET /screen-control/info`)
   - Click "Try it out"
   - Fill in parameters (if any)
   - Click "Execute"
   - See the response!

This is the **recommended method** - no code needed, just point and click!

## Method 2: Python Test Script

Use the provided test script:

1. **Install requests (if not already installed):**
   ```bash
   pip install requests
   ```

2. **Start the server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **Run the test script:**
   ```bash
   python test_screen_control.py
   ```

The script will:
- Get screen info
- Get mouse position
- Move mouse to center
- Take a screenshot
- Scroll
- Press keys

## Method 3: Using curl (Command Line)

Quick curl examples:

```bash
# Get screen info
curl http://localhost:8000/screen-control/info

# Get mouse position
curl http://localhost:8000/screen-control/mouse/position

# Move mouse (replace x, y with your screen coordinates)
curl -X POST http://localhost:8000/screen-control/mouse/move \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 300, "duration": 0.5}'

# Click mouse
curl -X POST http://localhost:8000/screen-control/mouse/click \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 300, "button": "left", "clicks": 1}'

# Take screenshot (saves to file)
curl http://localhost:8000/screen-control/screenshot -o screenshot.png

# Type text
curl -X POST "http://localhost:8000/screen-control/keyboard/type?text=Hello%20World"

# Press keys
curl -X POST http://localhost:8000/screen-control/keyboard/press \
  -H "Content-Type: application/json" \
  -d '{"keys": "ctrl+c", "presses": 1}'
```

## Method 4: Using httpie (Pretty curl)

If you have `httpie` installed:

```bash
# Get screen info
http GET localhost:8000/screen-control/info

# Move mouse
http POST localhost:8000/screen-control/mouse/move x:=500 y:=300 duration:=0.5

# Click
http POST localhost:8000/screen-control/mouse/click x:=500 y:=300 button:=left clicks:=1
```

## Method 5: Python Interactive Session

Quick Python testing:

```python
import requests

BASE = "http://localhost:8000/screen-control"

# Get screen info
response = requests.get(f"{BASE}/info")
print(response.json())

# Move mouse
requests.post(f"{BASE}/mouse/move", json={"x": 500, "y": 300, "duration": 0.5})

# Click
requests.post(f"{BASE}/mouse/click", json={"x": 500, "y": 300, "button": "left"})

# Take screenshot
response = requests.get(f"{BASE}/screenshot/base64")
print(f"Image: {response.json()['image'][:50]}...")
```

## Quick Start (Recommended)

1. **Start server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Open browser:**
   ```
   http://localhost:8000/docs
   ```

3. **Test `GET /screen-control/info`** - This is safe and won't move anything!

4. **Try other endpoints** - Be careful, they will control your screen!

## Safety Tips

- Start with read-only endpoints (`/info`, `/mouse/position`)
- Test mouse movements with small coordinates first
- Use `duration` parameter to make movements slower and visible
- Keep your hand near the mouse to stop if needed
- Test in a safe environment (not while working on important files)

## Troubleshooting

**Server won't start:**
```bash
# Install dependencies
pip install -r requirements.txt
```

**Import errors:**
```bash
# Make sure you're in the backend directory
cd backend
python -m uvicorn app.main:app --reload
```

**Permission errors (Linux):**
```bash
# You may need to install X11 dependencies
sudo apt-get install python3-tk python3-dev
```

**Mouse not moving:**
- Check that coordinates are within screen bounds
- Verify server is running and responding
- Check for error messages in server logs

