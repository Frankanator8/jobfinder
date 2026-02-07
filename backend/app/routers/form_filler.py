"""
API router for form filling agent
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.schemas.form_fields import FormFieldsRequest, FormFillResult
from app.agents.form_filler_agent import FormFillerAgent

router = APIRouter(prefix="/form-filler", tags=["form-filler"])

# Global agent instance (can be configured)
_agent: Optional[FormFillerAgent] = None


def get_agent() -> FormFillerAgent:
    """Get or create the form filler agent"""
    global _agent
    if _agent is None:
        _agent = FormFillerAgent()
    return _agent


@router.post("/fill", response_model=FormFillResult)
async def fill_form(request: FormFieldsRequest) -> FormFillResult:
    """
    Fill out form fields on the screen using the MCP agent.
    
    This endpoint takes a list of form fields with bounding boxes and field types,
    along with data to fill, and uses an AI agent to fill out the form.
    
    Args:
        request: FormFieldsRequest with fields and data
        
    Returns:
        FormFillResult with success status and details
    """
    try:
        agent = get_agent()
        result = agent.fill_form_from_request(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fill form: {str(e)}")


@router.post("/fill-simple")
async def fill_form_simple(
    fields: list[dict],
    data: dict[str, str],
    delay: float = 0.5
) -> dict:
    """
    Simplified form filling endpoint that accepts simple dictionaries.
    
    Args:
        fields: List of field dictionaries with keys: id, field_type, x, y, width, height, label (optional)
        data: Dictionary mapping field IDs to values
        delay: Delay between fields in seconds
        
    Returns:
        Result dictionary
    """
    try:
        from app.schemas.form_fields import FormField, BoundingBox
        
        # Convert simple dicts to FormField objects
        form_fields = []
        for field_dict in fields:
            bbox = BoundingBox(
                x=field_dict["x"],
                y=field_dict["y"],
                width=field_dict["width"],
                height=field_dict["height"],
            )
            form_field = FormField(
                id=field_dict["id"],
                field_type=field_dict["field_type"],
                bounding_box=bbox,
                label=field_dict.get("label"),
            )
            form_fields.append(form_field)
        
        request = FormFieldsRequest(
            fields=form_fields,
            data=data,
            delay_between_fields=delay,
        )
        
        agent = get_agent()
        result = agent.fill_form_from_request(request)
        
        return {
            "success": result.success,
            "filled_fields": result.filled_fields,
            "failed_fields": result.failed_fields,
            "errors": result.errors,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

