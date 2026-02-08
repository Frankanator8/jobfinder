"""
API router for async form filling agent
Uses bounding boxes from divselection.py, no screenshots, defaults to local:6767
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# Try to import AsyncFormFillerAgent
try:
    from app.agents.async_form_filler_agent import AsyncFormFillerAgent
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    AGENT_IMPORT_ERROR = str(e)
    AsyncFormFillerAgent = None

router = APIRouter(prefix="/async-form-filler", tags=["async-form-filler"])

# Global agent instance
_agent: Optional[AsyncFormFillerAgent] = None


def get_agent() -> AsyncFormFillerAgent:
    """Get or create the async form filler agent"""
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=f"Async form filler agent is not available. Import error: {AGENT_IMPORT_ERROR}"
        )
    global _agent
    if _agent is None:
        _agent = AsyncFormFillerAgent()
    return _agent


class AsyncFormFillRequest(BaseModel):
    """Request to fill form fields asynchronously"""
    url: str = Field(default="http://localhost:6767", description="URL to fill form on (default: localhost:6767)")
    data: Dict[str, Any] = Field(..., description="Data to fill into fields (keyed by field id, name, label, or type)")
    delay_between_fields: float = Field(default=0.3, description="Delay between field interactions in seconds")
    headless: bool = Field(default=True, description="Run browser in headless mode")


class AsyncFormFillResponse(BaseModel):
    """Response from async form filling"""
    success: bool = Field(..., description="Whether the operation was successful")
    filled_fields: list[str] = Field(default_factory=list, description="IDs of successfully filled fields")
    failed_fields: list[str] = Field(default_factory=list, description="IDs of fields that failed to fill")
    errors: list[str] = Field(default_factory=list, description="Error messages")
    output: Optional[str] = Field(None, description="Agent output")


@router.post("/fill", response_model=AsyncFormFillResponse)
async def fill_form(request: AsyncFormFillRequest) -> AsyncFormFillResponse:
    """
    Fill out form fields on a URL using bounding boxes from divselection.py.
    
    The agent will:
    1. Navigate to the URL
    2. Find form fields using divselection.py
    3. Use bounding boxes to click and type into fields
    4. No screenshots are taken - only bounding box information is used
    
    Default URL is http://localhost:6767
    """
    try:
        agent = get_agent()
        result = await agent.fill_form_from_url(
            url=request.url,
            data=request.data,
            delay_between_fields=request.delay_between_fields,
            headless=request.headless,
        )
        return AsyncFormFillResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fill form: {str(e)}"
        )


@router.post("/fill-with-fields")
async def fill_form_with_fields(
    fields: list[dict],
    data: Dict[str, Any],
    delay_between_fields: float = 0.3,
) -> AsyncFormFillResponse:
    """
    Fill form fields using provided field information (from divselection.py).
    
    This endpoint accepts fields that have already been detected.
    """
    try:
        from app.divselection import FormField as DivFormField
        
        # Convert dict fields to DivFormField objects
        div_fields = []
        for field_dict in fields:
            # Convert field_type string to FieldType enum
            from app.divselection import FieldType
            field_type_str = field_dict.get("field_type", "unknown")
            try:
                field_type = FieldType(field_type_str)
            except ValueError:
                field_type = FieldType.UNKNOWN
            
            div_field = DivFormField(
                element_id=field_dict.get("element_id", ""),
                field_type=field_type,
                label=field_dict.get("label", ""),
                name=field_dict.get("name", ""),
                placeholder=field_dict.get("placeholder", ""),
                required=field_dict.get("required", False),
                selector=field_dict.get("selector", ""),
                bounding_box=field_dict.get("bounding_box", {}),
            )
            div_fields.append(div_field)
        
        agent = get_agent()
        result = await agent.fill_form_fields(
            fields=div_fields,
            data=data,
            delay_between_fields=delay_between_fields,
        )
        return AsyncFormFillResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fill form: {str(e)}"
        )

