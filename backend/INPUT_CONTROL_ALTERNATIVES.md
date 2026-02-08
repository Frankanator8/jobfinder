# Input Control Alternatives

This document compares different approaches for controlling mouse and keyboard inputs, especially for async operations.

## Current Solution: PyAutoGUI + Thread Pool

**Pros:**
- Simple API
- Cross-platform
- Already implemented

**Cons:**
- Synchronous library (requires thread pool)
- Permission issues on macOS
- Can block event loop if not careful
- Not truly async

## Alternative 1: pynput (Recommended for OS-level control)

### Installation
```bash
pip install pynput
```

### Pros
- ✅ Better async support
- ✅ More reliable on macOS
- ✅ Better permission handling
- ✅ Can listen to events (mouse/keyboard)
- ✅ Cross-platform

### Cons
- Still needs thread pool for some operations
- Different API than pyautogui

### Example Implementation

```python
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import asyncio

class AsyncInputController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
    
    async def click(self, x: int, y: int, button: str = "left"):
        """Click at coordinates"""
        await asyncio.to_thread(self.mouse.click, Button.left if button == "left" else Button.right, 1)
        # Move first
        await asyncio.to_thread(self.mouse.position, (x, y))
        await asyncio.to_thread(self.mouse.click, Button.left if button == "left" else Button.right, 1)
    
    async def type_text(self, text: str):
        """Type text"""
        await asyncio.to_thread(self.keyboard.type, text)
    
    async def press_key(self, key: str):
        """Press key combination"""
        keys = key.split("+")
        if len(keys) == 1:
            await asyncio.to_thread(self.keyboard.press, Key[keys[0]])
            await asyncio.to_thread(self.keyboard.release, Key[keys[0]])
        else:
            # Handle combinations like ctrl+c
            pass
    
    async def get_position(self):
        """Get mouse position"""
        return await asyncio.to_thread(self.mouse.position)
    
    async def screenshot(self):
        """Take screenshot - still need PIL/pyautogui for this"""
        from PIL import ImageGrab
        return await asyncio.to_thread(ImageGrab.grab)
```

## Alternative 2: Playwright (Best for Browser Automation)

### Already Installed ✅

### Pros
- ✅ Native async/await
- ✅ No macOS permission issues
- ✅ Better for web automation
- ✅ Built-in screenshots
- ✅ Better error handling
- ✅ Can control browser, not just OS

### Cons
- Only works for browser automation
- Can't control desktop apps

### Example Implementation

```python
from playwright.async_api import async_playwright

async def fill_form_with_playwright(url: str, data: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url)
        
        # Fill form fields
        for field_id, value in data.items():
            await page.fill(f'#{field_id}', value)
        
        # Take screenshot
        screenshot = await page.screenshot()
        
        await browser.close()
        return screenshot
```

**This is probably the best option if you're automating web forms!**

## Alternative 3: pyobjc + Quartz (macOS Native)

### Installation
```bash
pip install pyobjc-framework-Quartz
```

### Pros
- ✅ Direct macOS API access
- ✅ Can be async
- ✅ More control
- ✅ Better performance

### Cons
- macOS only
- More complex API
- Requires Objective-C knowledge

### Example

```python
from Quartz import CGEventCreateMouseEvent, kCGEventLeftMouseDown, kCGEventLeftMouseUp
from Quartz import kCGHIDEventTap, kCGEventMouseMoved
import asyncio

async def native_click(x, y):
    def _click():
        # Create mouse down event
        event = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), kCGHIDEventTap)
        # Post event
        # ... (more complex)
    
    await asyncio.to_thread(_click)
```

## Alternative 4: AppleScript (macOS Only)

### Pros
- ✅ Simple for basic operations
- ✅ Can be async via subprocess
- ✅ Native macOS

### Cons
- macOS only
- Limited functionality
- String-based (error-prone)

### Example

```python
import subprocess
import asyncio

async def applescript_click(x, y):
    script = f'''
    tell application "System Events"
        click at {{{x}, {y}}}
    end tell
    '''
    proc = await asyncio.create_subprocess_exec(
        'osascript', '-e', script,
        stdout=asyncio.subprocess.PIPE
    )
    await proc.wait()
```

## Recommendation

### For Web Form Automation: **Use Playwright**
- You already have it installed
- Native async
- No permission issues
- Better suited for your use case

### For OS-level Control: **Use pynput**
- Better than pyautogui
- More reliable
- Better async support

### Hybrid Approach
- Use Playwright for browser automation (forms on websites)
- Use pynput for desktop app control (if needed)
- Keep pyautogui as fallback

## Migration Path

1. **Short term**: Keep current pyautogui + thread pool (already implemented)
2. **Medium term**: Add Playwright for web form filling (better fit)
3. **Long term**: Consider pynput if you need more OS-level control

## Code Example: Playwright Integration

Since you're already using Playwright for field detection, you could extend it:

```python
# In your form filler agent
from playwright.async_api import async_playwright

async def fill_form_playwright(url: str, fields: list, data: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url)
        
        for field in fields:
            field_id = field.id
            value = data.get(field_id)
            
            if value:
                # Use Playwright's native selectors
                selector = f'#{field_id}'  # or use field attributes
                await page.fill(selector, value)
        
        # Take screenshot
        screenshot = await page.screenshot()
        
        await browser.close()
        return screenshot
```

This would eliminate the need for screen coordinates and macOS permissions entirely!

