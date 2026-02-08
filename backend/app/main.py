from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import asyncio

# Load environment variables from .env file
load_dotenv()

from app.routers import health, screen_control, fields, scraper
from app.dbmanager import db
from app.agents.async_form_filler_agent import AsyncFormFillerAgent

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

# Queue processor settings
QUEUE_POLL_INTERVAL = 5  # seconds between polls
queue_processor_running = False


async def process_queue_item(queue_item: dict) -> bool:
    """
    Process a single queue item.

    Args:
        queue_item: Dictionary containing application_id, applicant_id, and _doc_id

    Returns:
        True if processed successfully, False otherwise
    """
    application_id = queue_item.get('application_id')
    applicant_id = queue_item.get('applicant_id')
    doc_id = queue_item.get('_doc_id')

    print(f"[QueueProcessor] Processing: application_id={application_id}, applicant_id={applicant_id}")

    try:
        # Mark as processing
        await db.update_queue_item_status(doc_id, 'processing')

        # Get user data
        user_data = await db.get_user_data(applicant_id)
        if not user_data:
            print(f"[QueueProcessor] No user data found for applicant: {applicant_id}")
            await db.update_queue_item_status(doc_id, 'failed', 'User data not found')
            return False

        # Get job application data
        job_application = await db.get_job_application(application_id)
        if not job_application:
            print(f"[QueueProcessor] No job application found: {application_id}")
            await db.update_queue_item_status(doc_id, 'failed', 'Job application not found')
            return False

        print(f"[QueueProcessor] User data: {user_data}")
        print(f"[QueueProcessor] Job application: {job_application}")

        # big_data = {**user_data.items(), **job_application.items()}
        # agent = AsyncFormFillerAgent()
        # result = await agent.fill_form_from_url(
        #     url=job_application.get('job_url'),
        #     data=big_data,
        #     delay_between_fields=0.3,
        #     headless=True
        # )
        # if result["success"]:
        #     await db.update_queue_item_status(doc_id, 'completed')
        # else:
        #     await db.update_queue_item_status(doc_id, 'failed', result.get("error", "Unknown error"))

        await asyncio.sleep(5)
        await db.update_queue_item_status(doc_id, 'completed')

        print(f"[QueueProcessor] Successfully processed queue item: {doc_id}")
        return True

    except Exception as e:
        print(f"[QueueProcessor] Error processing queue item {doc_id}: {e}")
        await db.update_queue_item_status(doc_id, 'failed', str(e))
        return False


async def queue_processor():
    """
    Background task that continuously polls the queue collection
    and processes the oldest item.
    """
    global queue_processor_running
    queue_processor_running = True

    print("[QueueProcessor] Starting queue processor...")

    while queue_processor_running:
        try:
            # Get the oldest queue item
            queue_item = await db.get_oldest_queue_item()

            if queue_item:
                # Check if it's already being processed
                status = queue_item.get('status')
                if status in ['processing', 'completed', 'failed']:
                    print(f"[QueueProcessor] Skipping item with status: {status}")
                else:
                    await process_queue_item(queue_item)
            else:
                print("[QueueProcessor] Queue is empty, waiting...")

        except Exception as e:
            print(f"[QueueProcessor] Error in queue processor: {e}")

        # Wait before next poll
        await asyncio.sleep(QUEUE_POLL_INTERVAL)

    print("[QueueProcessor] Queue processor stopped.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Start the queue processor
    task = asyncio.create_task(queue_processor())
    print("[Lifespan] Queue processor task created")

    yield

    # Shutdown: Stop the queue processor
    global queue_processor_running
    queue_processor_running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("[Lifespan] Queue processor task cancelled")


app = FastAPI(
    title="DF26 Backend",
    description="FastAPI backend service with MCP form filling agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(fields.router)
app.include_router(screen_control.router)
app.include_router(scraper.router)

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


@app.get("/queue/status")
async def queue_status():
    """Get the current status of the queue processor."""
    try:
        pending_count = await db.get_pending_queue_items_count()
        return {
            "running": queue_processor_running,
            "poll_interval_seconds": QUEUE_POLL_INTERVAL,
            "pending_items": pending_count
        }
    except Exception as e:
        return {
            "running": queue_processor_running,
            "poll_interval_seconds": QUEUE_POLL_INTERVAL,
            "error": str(e)
        }


