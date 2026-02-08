"""
Async screen control tools that directly control mouse and keyboard using pyautogui.
These tools work asynchronously and don't require HTTP API calls.
"""
import asyncio
from typing import Optional
import pyautogui

try:
    from langchain_core.tools import BaseTool
except ImportError:
    from langchain.tools import BaseTool

from pydantic import BaseModel, Field

# Configure pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05  # Reduced pause for faster execution


class MoveMouseInput(BaseModel):
    """Input for moving mouse"""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    duration: float = Field(default=0.3, description="Duration of movement in seconds")


class ClickMouseInput(BaseModel):
    """Input for clicking mouse"""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    button: str = Field(default="left", description="Mouse button: left, right, or middle")
    clicks: int = Field(default=1, description="Number of clicks")


class TypeTextInput(BaseModel):
    """Input for typing text"""
    text: str = Field(..., description="Text to type")
    interval: Optional[float] = Field(default=None, description="Interval between keystrokes in seconds")


class PressKeyInput(BaseModel):
    """Input for pressing keys"""
    keys: str = Field(..., description="Key(s) to press, e.g., 'enter', 'tab', 'backspace'. NOTE: 'a', 'delete', and 'ctrl+a' are disabled.")
    presses: int = Field(default=1, description="Number of times to press")


class FillFieldInput(BaseModel):
    """Input for filling a field"""
    x: int = Field(..., description="X coordinate of field center")
    y: int = Field(..., description="Y coordinate of field center")
    text: str = Field(..., description="Text to fill")
    field_type: str = Field(default="text", description="Type of field: text, email, textarea, select, etc.")


class ScrollInput(BaseModel):
    """Input for scrolling"""
    clicks: int = Field(..., description="Number of scroll clicks (positive=down, negative=up). MUST be non-zero (at least 1 or -1).")
    x: Optional[int] = Field(None, description="X coordinate to scroll at (optional)")
    y: Optional[int] = Field(None, description="Y coordinate to scroll at (optional)")


class GetScreenInfoInput(BaseModel):
    """Input for getting screen info (no parameters needed)"""
    class Config:
        extra = "forbid"


class MoveMouseTool(BaseTool):
    """Tool to move mouse cursor asynchronously"""
    name = "move_mouse"
    description = "Move mouse cursor to specified coordinates. WAIT for this to complete before next action. Input: x, y coordinates and optional duration in seconds."
    args_schema = MoveMouseInput
    
    def _run(self, x: int, y: int, duration: float = 0.3) -> str:
        """Execute the tool synchronously"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return f"Mouse moved to ({x}, {y})"
        except Exception as e:
            return f"Error moving mouse: {str(e)}"
    
    async def _arun(self, x: int, y: int, duration: float = 0.1) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run, x, y, duration)
        await asyncio.sleep(0.05)  # Reduced wait after moving mouse
        return result


class ClickMouseTool(BaseTool):
    """Tool to click mouse asynchronously"""
    name = "click_mouse"
    description = "Click mouse at specified coordinates. WAIT for this to complete (0.1s delay) before next action. NOTE: Triple click (clicks=3) is disabled. Input: x, y coordinates, button (left/right/middle), and number of clicks (max 2)."
    args_schema = ClickMouseInput
    
    def _run(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Execute the tool synchronously"""
        try:
            # Triple click is disabled
            if clicks == 3:
                return "Triple click is disabled. Cannot perform triple click."
            pyautogui.click(x, y, button=button, clicks=clicks)
            return f"Mouse {button} clicked {clicks} time(s) at ({x}, {y})"
        except Exception as e:
            return f"Error clicking mouse: {str(e)}"
    
    async def _arun(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Execute the tool asynchronously"""
        # Triple click is disabled
        if clicks == 3:
            return "Triple click is disabled. Cannot perform triple click."
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run, x, y, button, clicks)
        await asyncio.sleep(0.1)  # Reduced wait after clicking
        return result


class TypeTextTool(BaseTool):
    """Tool to type text asynchronously"""
    name = "type_text"
    description = "Type text at current cursor position. WAIT for this to complete (0.1s delay) before next action. Input: text to type and optional interval between keystrokes."
    args_schema = TypeTextInput
    
    def _run(self, text: str, interval: Optional[float] = None) -> str:
        """Execute the tool synchronously"""
        try:
            # Use default interval if None is provided
            if interval is None:
                interval = 0.05  # Default interval between keystrokes
            pyautogui.write(text, interval=interval)
            return f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}"
        except Exception as e:
            return f"Error typing text: {str(e)}"
    
    async def _arun(self, text: str, interval: Optional[float] = None) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        # Use default interval if None is provided
        if interval is None:
            interval = 0.05
        result = await loop.run_in_executor(None, self._run, text, interval)
        await asyncio.sleep(0.1)  # Reduced wait after typing
        return result


class PressKeyTool(BaseTool):
    """Tool to press keyboard keys asynchronously"""
    name = "press_key"
    description = "Press keyboard key(s). WAIT for this to complete (0.1s delay) before next action. CRITICAL: 'a' key, 'delete' key, and 'ctrl+a' are DISABLED and will return an error if attempted. DO NOT use these keys. Supports combinations like 'enter', 'tab', 'backspace', 'escape'. Input: keys to press."
    args_schema = PressKeyInput
    
    def _run(self, keys: str, presses: int = 1) -> str:
        """Execute the tool synchronously"""
        try:
            # Disable 'a' key, 'delete' key, and Ctrl+A combinations
            keys_lower = keys.lower()
            if keys_lower in ['a', 'delete', 'del'] or 'ctrl+a' in keys_lower or 'ctrl+a' in keys_lower.replace(' ', ''):
                return f"Key '{keys}' is disabled. Cannot press this key."
            for _ in range(presses):
                pyautogui.press(keys)
            return f"Pressed '{keys}' {presses} time(s)"
        except Exception as e:
            return f"Error pressing key: {str(e)}"
    
    async def _arun(self, keys: str, presses: int = 1) -> str:
        """Execute the tool asynchronously"""
        # Disable 'a' key, 'delete' key, and Ctrl+A combinations
        keys_lower = keys.lower()
        if keys_lower in ['a', 'delete', 'del'] or 'ctrl+a' in keys_lower or 'ctrl+a' in keys_lower.replace(' ', ''):
            return f"Key '{keys}' is disabled. Cannot press this key."
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run, keys, presses)
        await asyncio.sleep(0.1)  # Reduced wait after pressing keys
        return result


class FillFieldTool(BaseTool):
    """Tool to fill a field by clicking and typing"""
    name = "fill_field"
    description = "Fill a form field by clicking on it and typing text. This tool handles the full sequence with delays. WAIT for it to complete before next action. Input: x, y coordinates (center of field), text to fill, and field type."
    args_schema = FillFieldInput
    
    def _run(self, x: int, y: int, text: str, field_type: str = "text") -> str:
        """Execute the tool synchronously"""
        try:
            import time
            # Click to focus the field
            pyautogui.click(x, y, button="left", clicks=1)
            time.sleep(0.1)  # Small delay for focus
            
            # Clear existing text - DISABLED: Ctrl+A, delete, and triple click
            # pyautogui.hotkey('ctrl', 'a')  # DISABLED - cannot use 'a' key
            # time.sleep(0.05)
            # pyautogui.press('delete')  # DISABLED - cannot use 'delete' key
            # time.sleep(0.05)
            # pyautogui.click(x, y, button="left", clicks=3)  # DISABLED - triple click not allowed
            # Note: Field may still contain old text, new text will be appended
            
            # Type new text
            pyautogui.write(text, interval=0.05)
            
            return f"Successfully filled {field_type} field at ({x}, {y}) with '{text}'"
        except Exception as e:
            return f"Error filling field: {str(e)}"
    
    async def _arun(self, x: int, y: int, text: str, field_type: str = "text") -> str:
        """Execute the tool asynchronously with sequential delays"""
        try:
            loop = asyncio.get_event_loop()
            
            # Step 1: Click to focus the field
            # Use lambda to properly pass button and clicks as keyword arguments
            await loop.run_in_executor(None, lambda: pyautogui.click(x, y, button="left", clicks=1))
            await asyncio.sleep(0.1)  # Reduced wait for field to focus
            
            # Step 2: Clear existing text - DISABLED: Ctrl+A, delete, and triple click
            # await loop.run_in_executor(None, pyautogui.hotkey, 'ctrl', 'a')  # DISABLED - cannot use 'a' key
            # await asyncio.sleep(0.3)  # Wait after select all
            # await loop.run_in_executor(None, pyautogui.press, 'delete')  # DISABLED - cannot use 'delete' key
            # await asyncio.sleep(0.3)  # Wait after delete
            # await loop.run_in_executor(None, pyautogui.click, x, y, "left", 3)  # DISABLED - triple click not allowed
            # Note: Field may still contain old text, new text will be appended
            
            # Step 3: Type new text
            # Use lambda to properly pass interval as keyword argument
            await loop.run_in_executor(None, lambda: pyautogui.write(text, interval=0.05))
            await asyncio.sleep(0.1)  # Reduced wait after typing
            
            return f"Successfully filled {field_type} field at ({x}, {y}) with '{text}'"
        except Exception as e:
            return f"Error filling field: {str(e)}"


class GetScreenInfoTool(BaseTool):
    """Tool to get screen information"""
    name = "get_screen_info"
    description = "Get screen dimensions and current mouse position. Returns width, height, current_x, current_y. Use this to check if coordinates are within screen bounds. No input parameters needed."
    
    def _run(self) -> str:
        """Execute the tool synchronously"""
        try:
            width, height = pyautogui.size()
            current_x, current_y = pyautogui.position()
            return f"Screen: {width}x{height}, Mouse: ({current_x}, {current_y})"
        except Exception as e:
            return f"Error getting screen info: {str(e)}"
    
    async def _arun(self) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run)
        return result


class ScrollTool(BaseTool):
    """Tool to scroll mouse wheel"""
    name = "scroll"
    description = "Scroll mouse wheel ONLY if a field or button is NOT fully visible. DO NOT scroll if field is already fully visible. DO NOT use 0 clicks - that is invalid. Input: clicks (positive=down, negative=up, minimum 1 or -1), optional x,y coordinates to scroll at (recommended: use field center coordinates). Use 5-10 clicks for larger scrolls. Only scroll when Top Y < 0 (scroll up) or Bottom Y > screen height (scroll down). The tool will move mouse to the location first, then scroll."
    args_schema = ScrollInput
    
    def _run(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Execute the tool synchronously"""
        try:
            # Reject 0 clicks - makes no sense
            if clicks == 0:
                return "Error: Cannot scroll by 0 clicks. Use a positive number to scroll down or negative to scroll up (minimum 1 or -1)."
            
            # If coordinates provided, move mouse there first, then scroll
            if x is not None and y is not None:
                # Move mouse to the location first (helps with scrolling on some systems)
                pyautogui.moveTo(x, y, duration=0.1)
                import time
                time.sleep(0.1)  # Small delay after moving
                # Scroll at current mouse position (which is now at x, y)
                pyautogui.scroll(clicks)
            else:
                # Scroll at center of screen (more reliable)
                screen_width, screen_height = pyautogui.size()
                center_x, center_y = screen_width // 2, screen_height // 2
                pyautogui.moveTo(center_x, center_y, duration=0.1)
                import time
                time.sleep(0.1)  # Small delay after moving
                pyautogui.scroll(clicks)
            
            direction = "down" if clicks > 0 else "up"
            return f"Scrolled {abs(clicks)} clicks {direction}"
        except Exception as e:
            return f"Error scrolling: {str(e)}"
    
    async def _arun(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Execute the tool asynchronously"""
        # Reject 0 clicks - makes no sense
        if clicks == 0:
            return "Error: Cannot scroll by 0 clicks. Use a positive number to scroll down or negative to scroll up (minimum 1 or -1)."
        
        loop = asyncio.get_event_loop()
        
        try:
            # If coordinates provided, move mouse there first, then scroll
            if x is not None and y is not None:
                # Move mouse to the location first
                await loop.run_in_executor(None, lambda: pyautogui.moveTo(x, y, duration=0.1))
                await asyncio.sleep(0.05)  # Reduced delay after moving
                # Scroll at current mouse position (which is now at x, y)
                await loop.run_in_executor(None, pyautogui.scroll, clicks)
            else:
                # Scroll at center of screen (more reliable)
                screen_width, screen_height = await loop.run_in_executor(None, pyautogui.size)
                center_x, center_y = screen_width // 2, screen_height // 2
                await loop.run_in_executor(None, lambda: pyautogui.moveTo(center_x, center_y, duration=0.1))
                await asyncio.sleep(0.05)  # Reduced delay after moving
                await loop.run_in_executor(None, pyautogui.scroll, clicks)
            
            await asyncio.sleep(0.2)  # Reduced wait after scrolling
            direction = "down" if clicks > 0 else "up"
            return f"Scrolled {abs(clicks)} clicks {direction}"
        except Exception as e:
            return f"Error scrolling: {str(e)}"


class MoveMouseToFixedTool(BaseTool):
    """Tool to move mouse to hardcoded position (410, 105)"""
    name = "move_mouse_to_fixed"
    description = "Move mouse cursor to the hardcoded position (410, 105). This is used for URL copying workflow. WAIT for this to complete before next action."
    
    def _run(self) -> str:
        """Execute the tool synchronously"""
        try:
            pyautogui.moveTo(410, 105, duration=0.1)
            return "Mouse moved to fixed position (410, 105)"
        except Exception as e:
            return f"Error moving mouse to fixed position: {str(e)}"
    
    async def _arun(self) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run)
        await asyncio.sleep(0.05)  # Small wait after moving
        return result


class CopyTool(BaseTool):
    """Tool to copy text using Command+C (Mac) or Ctrl+C (Windows/Linux)"""
    name = "copy"
    description = "Copy text to clipboard using Command+C (Mac) or Ctrl+C (Windows/Linux). WAIT for this to complete (0.1s delay) before next action."
    
    def _run(self) -> str:
        """Execute the tool synchronously"""
        try:
            import platform
            if platform.system() == 'Darwin':  # Mac
                pyautogui.hotkey('command', 'c')
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'c')
            return "Text copied to clipboard"
        except Exception as e:
            return f"Error copying: {str(e)}"
    
    async def _arun(self) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run)
        await asyncio.sleep(0.1)  # Wait after copying
        return result


class TabTool(BaseTool):
    """Tool to press Command+Tab (Mac) or Ctrl+Tab (Windows/Linux) to move to next available field"""
    name = "tab"
    description = "Press Command+Tab (Mac) or Ctrl+Tab (Windows/Linux) to move focus to the next available input field/tab. WAIT for this to complete (0.1s delay) before next action."
    
    def _run(self) -> str:
        """Execute the tool synchronously"""
        try:
            import platform
            if platform.system() == 'Darwin':  # Mac
                pyautogui.hotkey('command', 'tab')
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'tab')
            return "Command+Tab (Mac) or Ctrl+Tab (Windows/Linux) pressed"
        except Exception as e:
            return f"Error pressing tab: {str(e)}"
    
    async def _arun(self) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run)
        await asyncio.sleep(0.1)  # Wait after tabbing
        return result


class PasteTool(BaseTool):
    """Tool to paste text using Command+V (Mac) or Ctrl+V (Windows/Linux)"""
    name = "paste"
    description = "Paste text from clipboard using Command+V (Mac) or Ctrl+V (Windows/Linux). WAIT for this to complete (0.2s delay) before next action."
    
    def _run(self) -> str:
        """Execute the tool synchronously"""
        try:
            import platform
            if platform.system() == 'Darwin':  # Mac
                pyautogui.hotkey('command', 'v')
            else:  # Windows/Linux
                pyautogui.hotkey('ctrl', 'v')
            return "Text pasted from clipboard"
        except Exception as e:
            return f"Error pasting: {str(e)}"
    
    async def _arun(self) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._run)
        await asyncio.sleep(0.2)  # Wait after pasting for content to be processed
        return result


def get_async_screen_control_tools() -> list[BaseTool]:
    """Get all async screen control tools"""
    return [
        GetScreenInfoTool(),
        MoveMouseTool(),
        ClickMouseTool(),
        TypeTextTool(),
        PressKeyTool(),
        ScrollTool(),
        FillFieldTool(),
        MoveMouseToFixedTool(),
        CopyTool(),
        TabTool(),
        PasteTool(),
    ]

