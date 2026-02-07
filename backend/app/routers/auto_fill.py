"""
Auto-fill router that chains field analysis with MCP agent
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from typing import Dict, Any, Optional

from app.divselection import analyze_url
from app.schemas.form_fields import FormField, BoundingBox, FormFieldsRequest, FormFillResult

# Try to import form filler agent
try:
    from app.agents.form_filler_agent import FormFillerAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    FormFillerAgent = None

router = APIRouter(prefix="/auto-fill", tags=["auto-fill"])


class AutoFillRequest(BaseModel):
    """Request to auto-fill a form on a website"""
    url: HttpUrl
    data: Dict[str, Any] = Field(..., description="Data to fill into fields (keyed by field name/id)")
    headless: bool = True
    screenshot_dir: Optional[str] = "screenshots"
    screenshot_before: bool = True
    screenshot_after: bool = True
    delay_between_fields: float = 0.5


class AutoFillResponse(BaseModel):
    """Response from auto-fill operation"""
    url: str
    analysis: Dict[str, Any]  # Results from field analysis
    fill_result: Optional[FormFillResult] = None
    success: bool
    message: str


def _map_field_type(detected_type: str) -> str:
    """
    Map detected field type to FormField field_type.
    
    Args:
        detected_type: Field type from analysis (e.g., "text", "email", "select")
        
    Returns:
        FormField field_type value
    """
    type_mapping = {
        "text": "text",
        "email": "email",
        "phone": "text",  # Phone fields are text inputs
        "name": "text",
        "textarea": "textarea",
        "select": "dropdown",
        "checkbox": "checkbox",
        "radio": "radio",
        "file": "file",
        "url": "text",
        "date": "date",
        "password": "password",
        "number": "number",
        "unknown": "unknown",
    }
    return type_mapping.get(detected_type.lower(), "text")


def _convert_field_info_to_form_field(field_info: Dict[str, Any], index: int) -> Optional[FormField]:
    """
    Convert FieldInfo from analysis to FormField for agent.
    
    Args:
        field_info: Field info dict from analyze_url
        index: Index for unique ID if needed
        
    Returns:
        FormField object or None if conversion fails
    """
    try:
        # Get bounding box
        bbox_dict = field_info.get("bounding_box", {})
        if not bbox_dict or not all(k in bbox_dict for k in ["x", "y", "width", "height"]):
            return None
        
        bbox = BoundingBox(
            x=int(bbox_dict["x"]),
            y=int(bbox_dict["y"]),
            width=int(bbox_dict["width"]),
            height=int(bbox_dict["height"])
        )
        
        # Get field ID (prefer element_id, then name, then generate)
        field_id = field_info.get("element_id") or field_info.get("name") or f"field_{index}"
        
        # Map field type
        detected_type = field_info.get("field_type", "unknown")
        field_type = _map_field_type(detected_type)
        
        # Get label
        label = field_info.get("label") or field_info.get("placeholder") or field_info.get("name", "")
        
        return FormField(
            id=field_id,
            field_type=field_type,
            bounding_box=bbox,
            label=label,
            required=field_info.get("required", False),
            value=field_info.get("value"),
            metadata={
                "selector": field_info.get("selector", ""),
                "placeholder": field_info.get("placeholder", ""),
                "detected_type": detected_type,
            }
        )
    except Exception as e:
        print(f"Error converting field: {e}")
        return None


@router.post("/analyze-and-fill", response_model=AutoFillResponse)
async def analyze_and_fill(request: AutoFillRequest) -> AutoFillResponse:
    """
    Analyze a website for form fields and automatically fill them using the MCP agent.
    
    This endpoint:
    1. Analyzes the website to detect form fields
    2. Converts detected fields to the format needed by the agent
    3. Uses the MCP agent to fill out the form using screen control
    
    Args:
        request: AutoFillRequest with URL and data to fill
        
    Returns:
        AutoFillResponse with analysis and fill results
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Form filler agent is not available. Check LANGCHAIN_FIX.md for troubleshooting."
        )
    
    try:
        # Step 1: Analyze the website to find fields
        analysis_result = await analyze_url(
            url=str(request.url),
            headless=request.headless,
            screenshot_dir=request.screenshot_dir or "screenshots"
        )
        
        # Step 2: Convert detected fields to FormField format
        form_fields = []
        for i, field_info in enumerate(analysis_result["fields"]):
            form_field = _convert_field_info_to_form_field(field_info, i)
            if form_field:
                form_fields.append(form_field)
        
        if not form_fields:
            return AutoFillResponse(
                url=str(request.url),
                analysis={
                    "field_count": analysis_result["field_count"],
                    "fields": analysis_result["fields"],
                    "screenshot_path": analysis_result["screenshot_path"],
                },
                fill_result=None,
                success=False,
                message="No valid form fields detected or converted"
            )
        
        # Step 3: Map data to field IDs
        # Try to match data keys to field names/ids
        mapped_data = {}
        for field in form_fields:
            # Try exact match first
            if field.id in request.data:
                mapped_data[field.id] = request.data[field.id]
            elif field.label and field.label.lower() in [k.lower() for k in request.data.keys()]:
                # Try label match
                for key, value in request.data.items():
                    if key.lower() == field.label.lower():
                        mapped_data[field.id] = value
                        break
            elif field.metadata.get("name") and field.metadata["name"] in request.data:
                # Try name match
                mapped_data[field.id] = request.data[field.metadata["name"]]
        
        # Step 4: Use MCP agent to fill the form
        fill_result = None
        if mapped_data:
            try:
                agent = FormFillerAgent()
                fill_request = FormFieldsRequest(
                    fields=form_fields,
                    data=mapped_data,
                    screenshot_before=request.screenshot_before,
                    screenshot_after=request.screenshot_after,
                    delay_between_fields=request.delay_between_fields
                )
                fill_result = agent.fill_form_from_request(fill_request)
            except Exception as e:
                return AutoFillResponse(
                    url=str(request.url),
                    analysis={
                        "field_count": analysis_result["field_count"],
                        "fields": analysis_result["fields"],
                        "screenshot_path": analysis_result["screenshot_path"],
                    },
                    fill_result=None,
                    success=False,
                    message=f"Failed to fill form: {str(e)}"
                )
        else:
            return AutoFillResponse(
                url=str(request.url),
                analysis={
                    "field_count": analysis_result["field_count"],
                    "fields": analysis_result["fields"],
                    "screenshot_path": analysis_result["screenshot_path"],
                },
                fill_result=None,
                success=False,
                message="No data matched to detected fields. Check field names/ids."
            )
        
        return AutoFillResponse(
            url=str(request.url),
            analysis={
                "field_count": analysis_result["field_count"],
                "fields": analysis_result["fields"],
                "screenshot_path": analysis_result["screenshot_path"],
                "field_summary": analysis_result.get("field_summary", {}),
            },
            fill_result=fill_result,
            success=fill_result.success if fill_result else False,
            message="Form analyzed and filled successfully" if fill_result and fill_result.success else "Form analyzed but filling failed"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-fill failed: {str(e)}")


@router.post("/from-analysis")
async def fill_from_analysis(
    analysis_result: Dict[str, Any],
    data: Dict[str, Any],
    screenshot_before: bool = True,
    screenshot_after: bool = True,
    delay: float = 0.5
) -> FormFillResult:
    """
    Fill form using pre-analyzed field data.
    
    Useful if you've already called /fields/analyze and want to fill the form.
    
    Args:
        analysis_result: Result from /fields/analyze endpoint
        data: Data to fill into fields
        screenshot_before: Take screenshot before filling
        screenshot_after: Take screenshot after filling
        delay: Delay between fields
        
    Returns:
        FormFillResult
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Form filler agent is not available."
        )
    
    try:
        # Convert analysis fields to FormField format
        form_fields = []
        for i, field_info in enumerate(analysis_result.get("fields", [])):
            form_field = _convert_field_info_to_form_field(field_info, i)
            if form_field:
                form_fields.append(form_field)
        
        if not form_fields:
            raise HTTPException(status_code=400, detail="No valid fields found in analysis result")
        
        # Map data to field IDs
        mapped_data = {}
        for field in form_fields:
            if field.id in data:
                mapped_data[field.id] = data[field.id]
            elif field.label and field.label.lower() in [k.lower() for k in data.keys()]:
                for key, value in data.items():
                    if key.lower() == field.label.lower():
                        mapped_data[field.id] = value
                        break
        
        # Fill using agent
        agent = FormFillerAgent()
        fill_request = FormFieldsRequest(
            fields=form_fields,
            data=mapped_data,
            screenshot_before=screenshot_before,
            screenshot_after=screenshot_after,
            delay_between_fields=delay
        )
        
        return agent.fill_form_from_request(fill_request)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fill form: {str(e)}")

