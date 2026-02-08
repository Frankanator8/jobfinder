"""
Example usage of the async form filler agent.

This agent:
- Uses bounding boxes from divselection.py (no screenshots)
- Controls mouse and keyboard directly (no HTTP API)
- Works asynchronously
- Defaults to localhost:6767
"""
import asyncio
from app.agents.async_form_filler_agent import AsyncFormFillerAgent


async def main():
    """Example: Fill a form on localhost:6767"""
    
    # Initialize the agent
    agent = AsyncFormFillerAgent()
    
    # Data to fill into the form
    form_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-1234",
        "firstname": "John",
        "lastname": "Doe",
    }
    
    # Fill the form (defaults to localhost:6767)
    result = await agent.fill_form_from_url(
        url="http://localhost:6767",
        data=form_data,
        delay_between_fields=0.3,
        headless=True,  # Set to False to see the browser
    )
    
    print("Form fill result:")
    print(f"Success: {result['success']}")
    print(f"Filled fields: {result['filled_fields']}")
    print(f"Failed fields: {result['failed_fields']}")
    if result['errors']:
        print(f"Errors: {result['errors']}")


if __name__ == "__main__":
    print("⚠️  WARNING: This will control your mouse and keyboard!")
    print("Make sure the form is visible on localhost:6767")
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        import time
        time.sleep(5)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")

