# macOS Permissions Setup for Screen Control

If you're experiencing timeouts when the agent tries to control your screen, it's likely a macOS permissions issue.

## Required Permissions

The screen control API needs two macOS permissions:

1. **Accessibility** - Required for mouse and keyboard control
2. **Screen Recording** - Required for taking screenshots

## How to Grant Permissions

### Step 1: Open System Settings

1. Click the Apple menu → **System Settings** (or **System Preferences** on older macOS)
2. Go to **Privacy & Security** (or **Security & Privacy**)

### Step 2: Grant Accessibility Permission

1. Click **Accessibility** in the left sidebar
2. Find your Python/Terminal application in the list
3. Enable the toggle next to it
4. If you don't see Python/Terminal, click the **+** button and add:
   - `/usr/bin/python3` or your Python executable
   - `/Applications/Utilities/Terminal.app` (if using Terminal)
   - Your IDE (VS Code, PyCharm, etc.) if running from there

### Step 3: Grant Screen Recording Permission

1. Click **Screen Recording** in the left sidebar
2. Find your Python/Terminal application in the list
3. Enable the toggle next to it
4. Add the same applications as above if needed

### Step 4: Restart Your Application

After granting permissions, **restart your Python process/server** for changes to take effect.

## Testing Permissions

You can test if permissions are working by:

1. **Manual API Test**: Call the endpoints directly via `localhost:8000/docs`
   - If these work but agent calls timeout, it's likely a different issue

2. **Python Test**:
   ```python
   import pyautogui
   pyautogui.position()  # Should work without errors
   pyautogui.screenshot()  # Should work without errors
   ```

3. **Check System Logs**: If permissions are missing, you'll see errors in Console.app

## Common Issues

### "Request timed out after 30s/60s/90s"

This usually means:
- Permissions not granted (most common)
- Python process needs to be restarted after granting permissions
- Wrong application selected in permissions (e.g., selected Python but running via uvicorn)

### "Failed to click mouse" / "Failed to type text"

These errors indicate missing Accessibility permission.

### Screenshot endpoints fail

This indicates missing Screen Recording permission.

## Troubleshooting

1. **Check which Python is running**:
   ```bash
   which python3
   ps aux | grep python
   ```

2. **Grant permissions to the correct executable**:
   - If using `uvicorn`, grant permissions to the Python executable that runs it
   - If using a virtual environment, grant permissions to that Python
   - If using an IDE, grant permissions to the IDE itself

3. **Restart everything**:
   - Stop your server
   - Restart Terminal/IDE
   - Start server again

4. **Verify permissions are active**:
   - System Settings → Privacy & Security → Accessibility
   - The toggle should be ON and the app should be listed

## Alternative: Run from Terminal

If permissions are still problematic, try running the server directly from Terminal (not an IDE):

```bash
cd backend
source venv/bin/activate  # if using venv
python -m uvicorn app.main:app --reload --port 8000
```

Then grant permissions to Terminal.app in System Settings.

## Note

macOS may prompt you to grant permissions the first time you try to use them. Make sure to click "Allow" when prompted.

