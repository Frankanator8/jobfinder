from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.routers import health, screen_control, fields

# Try to import form_filler, but make it optional
try:
    from app.routers import form_filler
    FORM_FILLER_AVAILABLE = True
except ImportError as e:
    FORM_FILLER_AVAILABLE = False
    FORM_FILLER_ERROR = str(e)
    form_filler = None

# Try to import auto_fill, but make it optional
try:
    from app.routers import auto_fill
    AUTO_FILL_AVAILABLE = True
except ImportError as e:
    AUTO_FILL_AVAILABLE = False
    AUTO_FILL_ERROR = str(e)
    auto_fill = None

# Try to import async_form_filler, but make it optional
try:
    from app.routers import async_form_filler
    ASYNC_FORM_FILLER_AVAILABLE = True
except ImportError as e:
    ASYNC_FORM_FILLER_AVAILABLE = False
    ASYNC_FORM_FILLER_ERROR = str(e)
    async_form_filler = None

app = FastAPI(
    title="DF26 Backend",
    description="FastAPI backend service with MCP form filling agent",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(fields.router)
app.include_router(screen_control.router)

# Only include form_filler router if it's available
if FORM_FILLER_AVAILABLE:
    app.include_router(form_filler.router)
else:
    # Add a warning endpoint
    @app.get("/form-filler/status")
    async def form_filler_status():
        return {
            "available": False,
            "error": FORM_FILLER_ERROR,
            "message": "Form filler agent is not available. Check LANGCHAIN_FIX.md for troubleshooting."
        }

# Only include auto_fill router if it's available
if AUTO_FILL_AVAILABLE:
    app.include_router(auto_fill.router)
else:
    # Add a warning endpoint
    @app.get("/auto-fill/status")
    async def auto_fill_status():
        return {
            "available": False,
            "error": AUTO_FILL_ERROR,
            "message": "Auto-fill is not available. Check LANGCHAIN_FIX.md for troubleshooting."
        }

# Only include async_form_filler router if it's available
if ASYNC_FORM_FILLER_AVAILABLE:
    app.include_router(async_form_filler.router)
else:
    # Add a warning endpoint
    @app.get("/async-form-filler/status")
    async def async_form_filler_status():
        return {
            "available": False,
            "error": ASYNC_FORM_FILLER_ERROR,
            "message": "Async form filler agent is not available."
        }


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to DF26 Backend"}
