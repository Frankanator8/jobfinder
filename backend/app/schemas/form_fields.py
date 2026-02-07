"""
Schemas for form field detection and interaction
"""
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict, Any


class BoundingBox(BaseModel):
    """Bounding box coordinates for a field"""
    x: int = Field(..., description="Top-left X coordinate")
    y: int = Field(..., description="Top-left Y coordinate")
    width: int = Field(..., description="Width of the field")
    height: int = Field(..., description="Height of the field")
    
    @property
    def center_x(self) -> int:
        """Center X coordinate"""
        return self.x + self.width // 2
    
    @property
    def center_y(self) -> int:
        """Center Y coordinate"""
        return self.y + self.height // 2
    
    @property
    def bottom_right_x(self) -> int:
        """Bottom-right X coordinate"""
        return self.x + self.width
    
    @property
    def bottom_right_y(self) -> int:
        """Bottom-right Y coordinate"""
        return self.y + self.height


class FormField(BaseModel):
    """Represents a form field on the screen"""
    id: str = Field(..., description="Unique identifier for the field")
    field_type: Literal[
        "text",
        "textarea",
        "dropdown",
        "checkbox",
        "radio",
        "button",
        "date",
        "number",
        "email",
        "password",
        "file",
        "unknown"
    ] = Field(..., description="Type of form field")
    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")
    label: Optional[str] = Field(None, description="Label or placeholder text")
    value: Optional[str] = Field(None, description="Current value in the field")
    required: bool = Field(default=False, description="Whether the field is required")
    options: Optional[List[str]] = Field(None, description="Options for dropdown/select fields")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class FormFieldsRequest(BaseModel):
    """Request to fill out form fields"""
    fields: List[FormField] = Field(..., description="List of form fields to fill")
    data: Dict[str, Any] = Field(..., description="Data to fill into fields (keyed by field id)")
    screenshot_before: bool = Field(default=False, description="Take screenshot before filling")
    screenshot_after: bool = Field(default=False, description="Take screenshot after filling")
    delay_between_fields: float = Field(default=0.5, description="Delay between field interactions in seconds")


class FormFillResult(BaseModel):
    """Result of form filling operation"""
    success: bool = Field(..., description="Whether the operation was successful")
    filled_fields: List[str] = Field(default_factory=list, description="IDs of successfully filled fields")
    failed_fields: List[str] = Field(default_factory=list, description="IDs of fields that failed to fill")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    screenshot_before: Optional[str] = Field(None, description="Base64 screenshot before filling")
    screenshot_after: Optional[str] = Field(None, description="Base64 screenshot after filling")

