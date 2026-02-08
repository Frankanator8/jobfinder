"""
API Router for form field analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.divselection import analyze_url, analyze_html, check_submission_status, check_html_submission_status


router = APIRouter(prefix="/fields", tags=["fields"])


class AnalyzeRequest(BaseModel):
    """Request model for URL field analysis."""
    url: HttpUrl
    headless: bool = True
    screenshot_dir: Optional[str] = "screenshots"


class AnalyzeHtmlRequest(BaseModel):
    """Request model for HTML content field analysis."""
    html_content: str
    base_url: str = "about:blank"
    headless: bool = True
    screenshot_dir: Optional[str] = "screenshots"


class SubmissionCheckRequest(BaseModel):
    """Request model for submission status check."""
    url: HttpUrl
    headless: bool = True
    screenshot_dir: Optional[str] = "screenshots"


class SubmissionCheckHtmlRequest(BaseModel):
    """Request model for HTML submission status check."""
    html_content: str
    base_url: str = "about:blank"
    headless: bool = True
    screenshot_dir: Optional[str] = "screenshots"


class SubmissionResult(BaseModel):
    """Result of submission detection."""
    status: str
    confidence: float
    indicators: list[str]
    confirmation_text: str
    success_elements: list[dict]
    error_elements: list[dict]
    screenshot_path: str
    url: str


class SubmissionResponse(BaseModel):
    """Response model for submission status check."""
    source: str
    submission_result: SubmissionResult


class FieldInfo(BaseModel):
    """Represents a detected form field."""
    element_id: str
    field_type: str
    label: str
    name: str
    placeholder: str
    required: bool
    selector: str
    bounding_box: dict
    options: list


class AnalyzeResponse(BaseModel):
    """Response model for field analysis."""
    source: str
    url: Optional[str] = None
    html_length: Optional[int] = None
    fields: list[FieldInfo]
    field_count: int
    screenshot_path: str
    field_summary: dict


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_application_fields(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a job application page URL to find and highlight form fields.

    Args:
        request: The analysis request containing the URL and options

    Returns:
        Analysis results including detected fields and screenshot path
    """
    try:
        result = await analyze_url(
            url=str(request.url),
            headless=request.headless,
            screenshot_dir=request.screenshot_dir or "screenshots"
        )

        return AnalyzeResponse(
            source=result["source"],
            url=result["url"],
            html_length=result.get("html_length"),
            fields=[FieldInfo(**f) for f in result["fields"]],
            field_count=result["field_count"],
            screenshot_path=result["screenshot_path"],
            field_summary=result["field_summary"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-html", response_model=AnalyzeResponse)
async def analyze_html_content(request: AnalyzeHtmlRequest) -> AnalyzeResponse:
    """
    Analyze HTML content to find and highlight form fields.

    Args:
        request: The analysis request containing the HTML content and options

    Returns:
        Analysis results including detected fields and screenshot path
    """
    try:
        result = await analyze_html(
            html_content=request.html_content,
            base_url=request.base_url,
            headless=request.headless,
            screenshot_dir=request.screenshot_dir or "screenshots"
        )

        return AnalyzeResponse(
            source=result["source"],
            url=result.get("url"),
            html_length=result.get("html_length"),
            fields=[FieldInfo(**f) for f in result["fields"]],
            field_count=result["field_count"],
            screenshot_path=result["screenshot_path"],
            field_summary=result["field_summary"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML analysis failed: {str(e)}")


@router.post("/check-submission", response_model=SubmissionResponse)
async def check_submission_status_endpoint(request: SubmissionCheckRequest) -> SubmissionResponse:
    """
    Check if a job application has been submitted by analyzing the page.

    Args:
        request: The submission check request containing the URL and options

    Returns:
        Submission status analysis results
    """
    try:
        result = await check_submission_status(
            url=str(request.url),
            headless=request.headless,
            screenshot_dir=request.screenshot_dir or "screenshots"
        )

        submission_result = result["submission_result"]

        return SubmissionResponse(
            source=result["source"],
            submission_result=SubmissionResult(**submission_result)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission check failed: {str(e)}")


@router.post("/check-submission-html", response_model=SubmissionResponse)
async def check_html_submission_status_endpoint(request: SubmissionCheckHtmlRequest) -> SubmissionResponse:
    """
    Check if a job application has been submitted by analyzing HTML content.

    Args:
        request: The submission check request containing the HTML content and options

    Returns:
        Submission status analysis results
    """
    try:
        result = await check_html_submission_status(
            html_content=request.html_content,
            base_url=request.base_url,
            headless=request.headless,
            screenshot_dir=request.screenshot_dir or "screenshots"
        )

        submission_result = result["submission_result"]

        return SubmissionResponse(
            source=result["source"],
            submission_result=SubmissionResult(**submission_result)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HTML submission check failed: {str(e)}")


