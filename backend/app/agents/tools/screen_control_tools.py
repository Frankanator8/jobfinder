"""
LangChain tools for screen control API
"""
import requests
from typing import Optional, Dict, Any
try:
    from langchain_core.tools import BaseTool
except ImportError:
    from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.schemas.form_fields import BoundingBox


class ScreenControlToolBase(BaseTool):
    """Base class for screen control tools"""
    base_url: str = "http://localhost:8000/screen-control"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to screen control API"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=kwargs.get("params"))
            else:
                response = requests.request(method, url, json=kwargs.get("json"), params=kwargs.get("params"))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "failed"}


class GetScreenInfoTool(ScreenControlToolBase):
    """Tool to get screen information"""
    name = "get_screen_info"
    description = "Get screen dimensions and current mouse position. Returns width, height, current_x, current_y."
    
    def _run(self) -> str:
        """Execute the tool"""
        result = self._make_request("GET", "/info")
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Screen: {result['width']}x{result['height']}, Mouse: ({result['current_x']}, {result['current_y']})"
    
    async def _arun(self) -> str:
        """Async execute"""
        return self._run()


class MoveMouseTool(ScreenControlToolBase):
    """Tool to move mouse cursor"""
    name = "move_mouse"
    description = "Move mouse cursor to specified coordinates. Input: x, y coordinates and optional duration in seconds."
    
    def _run(self, x: int, y: int, duration: float = 0.5) -> str:
        """Execute the tool"""
        result = self._make_request("POST", "/mouse/move", json={"x": x, "y": y, "duration": duration})
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", "Mouse moved successfully")
    
    async def _arun(self, x: int, y: int, duration: float = 0.5) -> str:
        """Async execute"""
        return self._run(x, y, duration)


class ClickMouseTool(ScreenControlToolBase):
    """Tool to click mouse"""
    name = "click_mouse"
    description = "Click mouse at specified coordinates. Input: x, y coordinates, button (left/right/middle), and number of clicks."
    
    def _run(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Execute the tool"""
        result = self._make_request("POST", "/mouse/click", json={
            "x": x, "y": y, "button": button, "clicks": clicks
        })
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", "Mouse clicked successfully")
    
    async def _arun(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Async execute"""
        return self._run(x, y, button, clicks)


class TypeTextTool(ScreenControlToolBase):
    """Tool to type text"""
    name = "type_text"
    description = "Type text at current cursor position. Input: text to type and optional interval between keystrokes."
    
    def _run(self, text: str, interval: Optional[float] = None) -> str:
        """Execute the tool"""
        params = {"text": text}
        if interval:
            params["interval"] = interval
        result = self._make_request("POST", "/keyboard/type", params=params)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", "Text typed successfully")
    
    async def _arun(self, text: str, interval: Optional[float] = None) -> str:
        """Async execute"""
        return self._run(text, interval)


class PressKeyTool(ScreenControlToolBase):
    """Tool to press keyboard keys"""
    name = "press_key"
    description = "Press keyboard key(s). Supports combinations like 'ctrl+c', 'enter', 'tab'. Input: keys to press."
    
    def _run(self, keys: str, presses: int = 1) -> str:
        """Execute the tool"""
        result = self._make_request("POST", "/keyboard/press", json={"keys": keys, "presses": presses})
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", "Key pressed successfully")
    
    async def _arun(self, keys: str, presses: int = 1) -> str:
        """Async execute"""
        return self._run(keys, presses)


class ScrollTool(ScreenControlToolBase):
    """Tool to scroll mouse wheel"""
    name = "scroll"
    description = "Scroll mouse wheel. Input: number of clicks (positive=up, negative=down), optional x,y coordinates, and horizontal flag."
    
    def _run(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None, horizontal: bool = False) -> str:
        """Execute the tool"""
        json_data = {"clicks": clicks, "horizontal": horizontal}
        if x is not None and y is not None:
            json_data["x"] = x
            json_data["y"] = y
        result = self._make_request("POST", "/mouse/scroll", json=json_data)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", "Scrolled successfully")
    
    async def _arun(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None, horizontal: bool = False) -> str:
        """Async execute"""
        return self._run(clicks, x, y, horizontal)


class TakeScreenshotTool(ScreenControlToolBase):
    """Tool to take screenshot"""
    name = "take_screenshot"
    description = "Take a screenshot of the screen or a region. Returns base64 encoded image. Optional region in format 'x,y,width,height'."
    
    def _run(self, region: Optional[str] = None) -> str:
        """Execute the tool"""
        params = {}
        if region:
            params["region"] = region
        result = self._make_request("GET", "/screenshot/base64", params=params)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("image", "")
    
    async def _arun(self, region: Optional[str] = None) -> str:
        """Async execute"""
        return self._run(region)


class FillTextFieldTool(ScreenControlToolBase):
    """Tool to fill a text field"""
    name = "fill_text_field"
    description = "Fill a text field by clicking it and typing. Input: bounding box (x, y, width, height) and text value."
    
    def _run(self, x: int, y: int, width: int, height: int, text: str) -> str:
        """Execute the tool"""
        # Calculate center of field
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Click to focus
        click_result = self._make_request("POST", "/mouse/click", json={"x": center_x, "y": center_y, "button": "left", "clicks": 1})
        if "error" in click_result:
            return f"Error clicking field: {click_result['error']}"
        
        # Clear existing text (select all and delete)
        self._make_request("POST", "/keyboard/press", json={"keys": "ctrl+a", "presses": 1})
        self._make_request("POST", "/keyboard/press", json={"keys": "delete", "presses": 1})
        
        # Type new text
        type_result = self._make_request("POST", "/keyboard/type", params={"text": text})
        if "error" in type_result:
            return f"Error typing text: {type_result['error']}"
        
        return f"Successfully filled text field at ({center_x}, {center_y}) with '{text}'"
    
    async def _arun(self, x: int, y: int, width: int, height: int, text: str) -> str:
        """Async execute"""
        return self._run(x, y, width, height, text)


class SelectDropdownOptionTool(ScreenControlToolBase):
    """Tool to select an option from a dropdown"""
    name = "select_dropdown_option"
    description = "Select an option from a dropdown field. Input: bounding box (x, y, width, height) and option text to select."
    
    def _run(self, x: int, y: int, width: int, height: int, option: str) -> str:
        """Execute the tool"""
        # Calculate center of field
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Click to open dropdown
        click_result = self._make_request("POST", "/mouse/click", json={"x": center_x, "y": center_y, "button": "left", "clicks": 1})
        if "error" in click_result:
            return f"Error clicking dropdown: {click_result['error']}"
        
        # Type the option (for searchable dropdowns) or use arrow keys
        # First try typing
        type_result = self._make_request("POST", "/keyboard/type", params={"text": option})
        if "error" not in type_result:
            # Press enter to select
            self._make_request("POST", "/keyboard/press", json={"keys": "enter", "presses": 1})
            return f"Successfully selected '{option}' from dropdown at ({center_x}, {center_y})"
        
        return f"Attempted to select '{option}' from dropdown at ({center_x}, {center_y})"
    
    async def _arun(self, x: int, y: int, width: int, height: int, option: str) -> str:
        """Async execute"""
        return self._run(x, y, width, height, option)


def get_screen_control_tools() -> list[BaseTool]:
    """Get all screen control tools"""
    return [
        GetScreenInfoTool(),
        MoveMouseTool(),
        ClickMouseTool(),
        TypeTextTool(),
        PressKeyTool(),
        ScrollTool(),
        TakeScreenshotTool(),
        FillTextFieldTool(),
        SelectDropdownOptionTool(),
    ]

