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
pyautogui.PAUSE = 0.05  # Small pause between actions


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
    keys: str = Field(..., description="Key(s) to press, e.g., 'ctrl+a', 'enter', 'tab'")
    presses: int = Field(default=1, description="Number of times to press")


class FillFieldInput(BaseModel):
    """Input for filling a field"""
    x: int = Field(..., description="X coordinate of field center")
    y: int = Field(..., description="Y coordinate of field center")
    text: str = Field(..., description="Text to fill")
    field_type: str = Field(default="text", description="Type of field: text, email, textarea, select, etc.")


class MoveMouseTool(BaseTool):
    """Tool to move mouse cursor asynchronously"""
    name = "move_mouse"
    description = "Move mouse cursor to specified coordinates. Input: x, y coordinates and optional duration in seconds."
    args_schema = MoveMouseInput
    
    def _run(self, x: int, y: int, duration: float = 0.3) -> str:
        """Execute the tool synchronously"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return f"Mouse moved to ({x}, {y})"
        except Exception as e:
            return f"Error moving mouse: {str(e)}"
    
    async def _arun(self, x: int, y: int, duration: float = 0.3) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, x, y, duration)


class ClickMouseTool(BaseTool):
    """Tool to click mouse asynchronously"""
    name = "click_mouse"
    description = "Click mouse at specified coordinates. Input: x, y coordinates, button (left/right/middle), and number of clicks."
    args_schema = ClickMouseInput
    
    def _run(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Execute the tool synchronously"""
        try:
            pyautogui.click(x, y, button=button, clicks=clicks)
            return f"Mouse {button} clicked {clicks} time(s) at ({x}, {y})"
        except Exception as e:
            return f"Error clicking mouse: {str(e)}"
    
    async def _arun(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, x, y, button, clicks)


class TypeTextTool(BaseTool):
    """Tool to type text asynchronously"""
    name = "type_text"
    description = "Type text at current cursor position. Input: text to type and optional interval between keystrokes."
    args_schema = TypeTextInput
    
    def _run(self, text: str, interval: Optional[float] = None) -> str:
        """Execute the tool synchronously"""
        try:
            pyautogui.write(text, interval=interval)
            return f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}"
        except Exception as e:
            return f"Error typing text: {str(e)}"
    
    async def _arun(self, text: str, interval: Optional[float] = None) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, text, interval)


class PressKeyTool(BaseTool):
    """Tool to press keyboard keys asynchronously"""
    name = "press_key"
    description = "Press keyboard key(s). Supports combinations like 'ctrl+a', 'enter', 'tab'. Input: keys to press."
    args_schema = PressKeyInput
    
    def _run(self, keys: str, presses: int = 1) -> str:
        """Execute the tool synchronously"""
        try:
            for _ in range(presses):
                pyautogui.press(keys)
            return f"Pressed '{keys}' {presses} time(s)"
        except Exception as e:
            return f"Error pressing key: {str(e)}"
    
    async def _arun(self, keys: str, presses: int = 1) -> str:
        """Execute the tool asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run, keys, presses)


class FillFieldTool(BaseTool):
    """Tool to fill a field by clicking and typing"""
    name = "fill_field"
    description = "Fill a form field by clicking on it and typing text. Input: x, y coordinates (center of field), text to fill, and field type."
    args_schema = FillFieldInput
    
    def _run(self, x: int, y: int, text: str, field_type: str = "text") -> str:
        """Execute the tool synchronously"""
        try:
            import time
            # Click to focus the field
            pyautogui.click(x, y, button="left", clicks=1)
            time.sleep(0.1)  # Small delay for focus
            
            # Clear existing text
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.05)
            pyautogui.press('delete')
            time.sleep(0.05)
            
            # Type new text
            pyautogui.write(text, interval=0.01)
            
            return f"Successfully filled {field_type} field at ({x}, {y}) with '{text}'"
        except Exception as e:
            return f"Error filling field: {str(e)}"
    
    async def _arun(self, x: int, y: int, text: str, field_type: str = "text") -> str:
        """Execute the tool asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            # Click to focus the field
            await loop.run_in_executor(None, pyautogui.click, x, y, "left", 1)
            await asyncio.sleep(0.1)  # Small delay for focus
            
            # Clear existing text
            await loop.run_in_executor(None, pyautogui.hotkey, 'ctrl', 'a')
            await asyncio.sleep(0.05)
            await loop.run_in_executor(None, pyautogui.press, 'delete')
            await asyncio.sleep(0.05)
            
            # Type new text
            await loop.run_in_executor(None, pyautogui.write, text, 0.01)
            
            return f"Successfully filled {field_type} field at ({x}, {y}) with '{text}'"
        except Exception as e:
            return f"Error filling field: {str(e)}"


def get_async_screen_control_tools() -> list[BaseTool]:
    """Get all async screen control tools"""
    return [
        MoveMouseTool(),
        ClickMouseTool(),
        TypeTextTool(),
        PressKeyTool(),
        FillFieldTool(),
    ]

