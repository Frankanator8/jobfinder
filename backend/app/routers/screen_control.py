"""
Screen Control API Router

This router provides endpoints for controlling the user's screen and mouse.
These endpoints allow an agent to:
- Get screen information
- Move the mouse cursor
- Perform mouse clicks
- Drag and drop operations
- Scroll the screen
- Take screenshots
- Press keyboard keys

WARNING: These endpoints provide full control over the user's screen.
Use with extreme caution and proper authentication.
"""
import io
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
import pyautogui

from app.schemas.screen_control import (
    MouseMoveRequest,
    MouseClickRequest,
    MouseDragRequest,
    MouseScrollRequest,
    KeyPressRequest,
    ScreenInfoResponse,
)

router = APIRouter(prefix="/screen-control", tags=["screen-control"])

# Safety settings - disable failsafe for API usage
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1  # Small pause between actions


@router.get("/info", response_model=ScreenInfoResponse)
async def get_screen_info() -> ScreenInfoResponse:
    """
    Get current screen information including size and mouse position.
    
    Returns:
        ScreenInfoResponse: Screen dimensions and current mouse position
    """
    try:
        width, height = pyautogui.size()
        current_x, current_y = pyautogui.position()
        
        return ScreenInfoResponse(
            width=width,
            height=height,
            current_x=current_x,
            current_y=current_y
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get screen info: {str(e)}")


@router.post("/mouse/move")
async def move_mouse(request: MouseMoveRequest) -> dict[str, str]:
    """
    Move the mouse cursor to a specific position.
    
    Args:
        request: MouseMoveRequest with x, y coordinates and optional duration
        
    Returns:
        Success message with new position
    """
    try:
        # Validate coordinates are within screen bounds
        screen_width, screen_height = pyautogui.size()
        if request.x < 0 or request.x >= screen_width:
            raise HTTPException(
                status_code=400,
                detail=f"X coordinate {request.x} is out of bounds (0-{screen_width-1})"
            )
        if request.y < 0 or request.y >= screen_height:
            raise HTTPException(
                status_code=400,
                detail=f"Y coordinate {request.y} is out of bounds (0-{screen_height-1})"
            )
        
        pyautogui.moveTo(request.x, request.y, duration=request.duration)
        current_x, current_y = pyautogui.position()
        
        return {
            "status": "success",
            "message": f"Mouse moved to ({request.x}, {request.y})",
            "current_position": f"({current_x}, {current_y})"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move mouse: {str(e)}")


@router.post("/mouse/click")
async def click_mouse(request: MouseClickRequest) -> dict[str, str]:
    """
    Perform a mouse click at a specific position or current position.
    
    Args:
        request: MouseClickRequest with optional coordinates and click details
        
    Returns:
        Success message
    """
    try:
        if request.x is not None and request.y is not None:
            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if request.x < 0 or request.x >= screen_width or request.y < 0 or request.y >= screen_height:
                raise HTTPException(
                    status_code=400,
                    detail=f"Coordinates ({request.x}, {request.y}) are out of bounds"
                )
            pyautogui.click(request.x, request.y, button=request.button, clicks=request.clicks, interval=request.interval)
        else:
            pyautogui.click(button=request.button, clicks=request.clicks, interval=request.interval)
        
        return {
            "status": "success",
            "message": f"Mouse {request.button} clicked {request.clicks} time(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to click mouse: {str(e)}")


@router.post("/mouse/drag")
async def drag_mouse(request: MouseDragRequest) -> dict[str, str]:
    """
    Drag the mouse from one position to another.
    
    Args:
        request: MouseDragRequest with start/end coordinates and drag details
        
    Returns:
        Success message
    """
    try:
        # Validate coordinates
        screen_width, screen_height = pyautogui.size()
        for coord_name, x, y in [
            ("start", request.start_x, request.start_y),
            ("end", request.end_x, request.end_y)
        ]:
            if x < 0 or x >= screen_width or y < 0 or y >= screen_height:
                raise HTTPException(
                    status_code=400,
                    detail=f"{coord_name} coordinates ({x}, {y}) are out of bounds"
                )
        
        pyautogui.drag(
            request.end_x - request.start_x,
            request.end_y - request.start_y,
            duration=request.duration,
            button=request.button,
            origin=(request.start_x, request.start_y)
        )
        
        return {
            "status": "success",
            "message": f"Mouse dragged from ({request.start_x}, {request.start_y}) to ({request.end_x}, {request.end_y})"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to drag mouse: {str(e)}")


@router.post("/mouse/scroll")
async def scroll_mouse(request: MouseScrollRequest) -> dict[str, str]:
    """
    Scroll the mouse wheel at a specific position or current position.
    
    Args:
        request: MouseScrollRequest with optional coordinates and scroll details
        
    Returns:
        Success message
    """
    try:
        if request.x is not None and request.y is not None:
            # Validate coordinates
            screen_width, screen_height = pyautogui.size()
            if request.x < 0 or request.x >= screen_width or request.y < 0 or request.y >= screen_height:
                raise HTTPException(
                    status_code=400,
                    detail=f"Coordinates ({request.x}, {request.y}) are out of bounds"
                )
            pyautogui.scroll(request.clicks, x=request.x, y=request.y)
        else:
            if request.horizontal:
                pyautogui.hscroll(request.clicks)
            else:
                pyautogui.scroll(request.clicks)
        
        return {
            "status": "success",
            "message": f"Scrolled {request.clicks} clicks {'horizontally' if request.horizontal else 'vertically'}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scroll: {str(e)}")


@router.get("/mouse/position")
async def get_mouse_position() -> dict[str, int]:
    """
    Get the current mouse cursor position.
    
    Returns:
        Current mouse X and Y coordinates
    """
    try:
        x, y = pyautogui.position()
        return {"x": x, "y": y}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mouse position: {str(e)}")


@router.post("/keyboard/press")
async def press_key(request: KeyPressRequest) -> dict[str, str]:
    """
    Press keyboard key(s). Supports key combinations like 'ctrl+c', 'shift+tab', etc.
    
    Args:
        request: KeyPressRequest with key(s) to press
        
    Returns:
        Success message
    """
    try:
        for _ in range(request.presses):
            pyautogui.press(request.keys, interval=request.interval)
        
        return {
            "status": "success",
            "message": f"Pressed '{request.keys}' {request.presses} time(s)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to press key: {str(e)}")


@router.post("/keyboard/type")
async def type_text(text: str, interval: Optional[float] = None) -> dict[str, str]:
    """
    Type text at the current cursor position.
    
    Args:
        text: Text to type
        interval: Optional delay between keystrokes in seconds
        
    Returns:
        Success message
    """
    try:
        pyautogui.write(text, interval=interval)
        return {
            "status": "success",
            "message": f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to type text: {str(e)}")


@router.get("/screenshot")
async def take_screenshot(
    region: Optional[str] = None,
    format: str = "png"
) -> Response:
    """
    Take a screenshot of the screen or a specific region.
    
    Args:
        region: Optional region in format "x,y,width,height" (e.g., "100,100,800,600")
        format: Image format (png, jpg, jpeg)
        
    Returns:
        Image file as response
    """
    try:
        if region:
            parts = region.split(",")
            if len(parts) != 4:
                raise HTTPException(
                    status_code=400,
                    detail="Region must be in format 'x,y,width,height'"
                )
            x, y, width, height = map(int, parts)
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
        else:
            screenshot = pyautogui.screenshot()
        
        # Convert to bytes
        img_io = io.BytesIO()
        screenshot.save(img_io, format=format.upper())
        img_io.seek(0)
        
        return StreamingResponse(
            io.BytesIO(img_io.read()),
            media_type=f"image/{format.lower()}",
            headers={"Content-Disposition": "attachment; filename=screenshot.png"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to take screenshot: {str(e)}")


@router.get("/screenshot/base64")
async def take_screenshot_base64(
    region: Optional[str] = None
) -> dict[str, str]:
    """
    Take a screenshot and return it as a base64-encoded string.
    
    Args:
        region: Optional region in format "x,y,width,height"
        
    Returns:
        Base64-encoded image string
    """
    try:
        if region:
            parts = region.split(",")
            if len(parts) != 4:
                raise HTTPException(
                    status_code=400,
                    detail="Region must be in format 'x,y,width,height'"
                )
            x, y, width, height = map(int, parts)
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
        else:
            screenshot = pyautogui.screenshot()
        
        # Convert to base64
        img_io = io.BytesIO()
        screenshot.save(img_io, format="PNG")
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.read()).decode("utf-8")
        
        return {
            "status": "success",
            "image": f"data:image/png;base64,{img_base64}",
            "format": "png"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to take screenshot: {str(e)}")

