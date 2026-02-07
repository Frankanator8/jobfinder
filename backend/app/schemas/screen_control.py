from pydantic import BaseModel, Field
from typing import Optional, Literal


class MouseMoveRequest(BaseModel):
    """Request to move mouse to a specific position"""
    x: int = Field(..., description="X coordinate (0-based)")
    y: int = Field(..., description="Y coordinate (0-based)")
    duration: Optional[float] = Field(
        default=0.0,
        description="Duration in seconds for the movement (0 for instant)",
        ge=0.0
    )


class MouseClickRequest(BaseModel):
    """Request to click at a specific position"""
    x: Optional[int] = Field(None, description="X coordinate (if None, uses current position)")
    y: Optional[int] = Field(None, description="Y coordinate (if None, uses current position)")
    button: Literal["left", "right", "middle"] = Field(
        default="left",
        description="Mouse button to click"
    )
    clicks: int = Field(default=1, description="Number of clicks", ge=1, le=3)
    interval: Optional[float] = Field(
        default=None,
        description="Interval between clicks in seconds"
    )


class MouseDragRequest(BaseModel):
    """Request to drag mouse from one position to another"""
    start_x: int = Field(..., description="Starting X coordinate")
    start_y: int = Field(..., description="Starting Y coordinate")
    end_x: int = Field(..., description="Ending X coordinate")
    end_y: int = Field(..., description="Ending Y coordinate")
    duration: Optional[float] = Field(
        default=0.5,
        description="Duration in seconds for the drag",
        ge=0.0
    )
    button: Literal["left", "right", "middle"] = Field(
        default="left",
        description="Mouse button to hold during drag"
    )


class MouseScrollRequest(BaseModel):
    """Request to scroll mouse"""
    x: Optional[int] = Field(None, description="X coordinate (if None, uses current position)")
    y: Optional[int] = Field(None, description="Y coordinate (if None, uses current position)")
    clicks: int = Field(..., description="Number of scroll clicks (positive=up, negative=down)")
    horizontal: bool = Field(default=False, description="Whether to scroll horizontally")


class KeyPressRequest(BaseModel):
    """Request to press keyboard keys"""
    keys: str = Field(..., description="Key(s) to press (e.g., 'ctrl+c', 'enter', 'a')")
    presses: int = Field(default=1, description="Number of times to press", ge=1)
    interval: Optional[float] = Field(
        default=None,
        description="Interval between presses in seconds"
    )


class ScreenInfoResponse(BaseModel):
    """Response containing screen information"""
    width: int = Field(..., description="Screen width in pixels")
    height: int = Field(..., description="Screen height in pixels")
    current_x: int = Field(..., description="Current mouse X position")
    current_y: int = Field(..., description="Current mouse Y position")

