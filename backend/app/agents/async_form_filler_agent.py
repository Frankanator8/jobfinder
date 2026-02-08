"""
Async Form Filler Agent - Uses bounding boxes from divselection.py to fill forms.
Controls mouse and keyboard directly (no HTTP API, no screenshots).
"""
import asyncio
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    try:
        from langchain_core.agents import AgentExecutor
        from langchain.agents import create_openai_tools_agent
    except ImportError:
        from langchain.agents.agent_executor import AgentExecutor
        from langchain.agents import create_openai_tools_agent

from langchain_openai import ChatOpenAI
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.tools.async_screen_control_tools import get_async_screen_control_tools
from app.divselection import FormField as DivFormField, FieldType


class AsyncFormFillerAgent:
    """
    Async agent that fills out form fields using bounding boxes from divselection.py.
    Only uses mouse clicks and keyboard typing - no screenshots.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the async form filler agent
        
        Args:
            model_name: OpenAI model to use
            temperature: Model temperature
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.openai_api_key,
        )
        
        # Get async tools
        self.tools = get_async_screen_control_tools()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert form-filling agent that controls a user's screen to fill out web forms.

Your capabilities:
- Move the mouse cursor to specific coordinates
- Click on form fields using their bounding box center coordinates
- Type text into text fields
- Clear existing text before typing (Ctrl+A, Delete)
- Handle different field types appropriately

CRITICAL RULES - EXECUTE SEQUENTIALLY:
1. You will receive bounding boxes (x, y, width, height) for each field
2. Calculate the center of each field: center_x = x + width/2, center_y = y + height/2
3. Use the center coordinates to click on fields
4. ALWAYS execute ONE action at a time - wait for each tool to complete before calling the next
5. For each field, follow this EXACT sequence:
   a. Click on the field center coordinates (wait for it to complete)
   b. Wait 0.5 seconds
   c. Press Ctrl+A to select all (wait for it to complete)
   d. Wait 0.3 seconds
   e. Press Delete to clear (wait for it to complete)
   f. Wait 0.3 seconds
   g. Type the text (wait for it to complete)
   h. Wait 0.5 seconds before moving to next field
6. NEVER call multiple tools in rapid succession - each tool call must complete before the next
7. Fill fields ONE AT A TIME in the order provided
8. Wait at least 0.5 seconds between filling different fields
9. Do NOT take screenshots - you only have bounding box information
10. The tools already have built-in delays - do NOT add extra delays, just use them sequentially

Field types you can handle:
- text, email, phone, name: Regular text input fields - click, clear, type
- textarea: Multi-line text fields - click, clear, type
- select, dropdown: Dropdown fields - click to open, type option, press Enter
- checkbox: Checkbox fields - click to toggle
- radio: Radio button fields - click to select
- file: File upload fields - click to open file dialog (you can't upload files, just click)
- date: Date input fields - click, clear, type date
- password: Password fields - click, clear, type (text will be hidden)

You will receive:
- Field bounding boxes (x, y, width, height) - these are screen coordinates
- Field types - what kind of field it is
- Data to fill - the values to put in each field

Be precise with coordinates and methodical in your approach. Fill one field at a time."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        try:
            self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=50,
            )
        except Exception as e:
            self.agent = None
            self.agent_executor = None
            self._agent_error = str(e)
    
    async def fill_form_fields(
        self,
        fields: List[DivFormField],
        data: Dict[str, Any],
        delay_between_fields: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Fill out form fields using the agent asynchronously
        
        Args:
            fields: List of FormField objects from divselection.py
            data: Dictionary mapping field identifiers to values
            delay_between_fields: Delay between field interactions in seconds
            
        Returns:
            Dictionary with success status and details
        """
        if self.agent_executor is None:
            raise RuntimeError(f"Agent not initialized: {getattr(self, '_agent_error', 'Unknown error')}")
        
        filled_fields = []
        failed_fields = []
        errors = []
        
        # Build instruction for agent
        field_descriptions = []
        for field in fields:
            # Try to match field with data using various identifiers
            field_id = field.element_id
            field_name = field.name
            field_label = field.label.lower() if field.label else ""
            
            # Find matching value in data
            value = None
            for key, val in data.items():
                key_lower = key.lower()
                if (key_lower == field_id.lower() or 
                    key_lower == field_name.lower() or 
                    key_lower in field_label or
                    field_label and key_lower in field_label):
                    value = val
                    break
            
            # If no match found, try field type matching
            if value is None:
                field_type_key = field.field_type.value
                if field_type_key in data:
                    value = data[field_type_key]
                elif field_type_key in ["name", "email", "phone"]:
                    # Try common variations
                    for key in data.keys():
                        if field_type_key in key.lower():
                            value = data[key]
                            break
            
            if value is None:
                continue  # Skip fields without data
            
            bbox = field.bounding_box
            center_x = bbox.get("x", 0) + bbox.get("width", 0) // 2
            center_y = bbox.get("y", 0) + bbox.get("height", 0) // 2
            
            field_descriptions.append(
                f"Field '{field_id}' ({field.label or field_name or 'Unnamed'}):\n"
                f"  Type: {field.field_type.value}\n"
                f"  Bounding box: x={bbox.get('x')}, y={bbox.get('y')}, width={bbox.get('width')}, height={bbox.get('height')}\n"
                f"  Center coordinates: ({center_x}, {center_y})\n"
                f"  Value to fill: {value}\n"
                f"  Required: {field.required}"
            )
        
        if not field_descriptions:
            return {
                "success": False,
                "filled_fields": [],
                "failed_fields": [f.element_id for f in fields],
                "errors": ["No matching data found for any fields"],
            }
        
        instruction = f"""Fill out the following form fields on the screen using their bounding box coordinates:

{chr(10).join(field_descriptions)}

CRITICAL INSTRUCTIONS - EXECUTE SEQUENTIALLY:
1. Fill fields ONE AT A TIME in the order listed - do NOT rush
2. For EACH field, follow this exact sequence:
   - Step 1: Click on the field using center coordinates (use click_mouse tool)
   - Step 2: WAIT for the click to complete (the tool handles this)
   - Step 3: Press Ctrl+A to select all text (use press_key tool with 'ctrl+a')
   - Step 4: WAIT for the key press to complete
   - Step 5: Press Delete to clear (use press_key tool with 'delete')
   - Step 6: WAIT for the delete to complete
   - Step 7: Type the value (use type_text tool)
   - Step 8: WAIT for typing to complete
   - Step 9: Wait an additional {delay_between_fields} seconds before starting the next field
3. NEVER call multiple tools at once - each tool must complete before calling the next
4. Be precise with coordinates
5. The tools have built-in delays - trust them and execute sequentially

Start with the FIRST field only. Complete it fully before moving to the next."""
        
        try:
            # Execute agent asynchronously
            # Try ainvoke first, fall back to running invoke in executor
            if hasattr(self.agent_executor, 'ainvoke'):
                result = await self.agent_executor.ainvoke({
                    "input": instruction,
                    "chat_history": [],
                })
            else:
                # Fall back to running invoke in executor
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.agent_executor.invoke,
                    {
                        "input": instruction,
                        "chat_history": [],
                    }
                )
            
            # Parse result
            output = result.get("output", "")
            
            # Determine which fields were filled based on output
            for field in fields:
                field_id = field.element_id
                if field_id in output.lower() or "success" in output.lower() or field_id in str(data.keys()):
                    filled_fields.append(field_id)
                else:
                    failed_fields.append(field_id)
            
            # If we couldn't determine, assume all were attempted
            if not filled_fields and not failed_fields:
                filled_fields = [f.element_id for f in fields]
            
            return {
                "success": len(filled_fields) > 0 and len(failed_fields) == 0,
                "filled_fields": filled_fields,
                "failed_fields": failed_fields,
                "errors": errors,
                "output": output,
            }
            
        except Exception as e:
            errors.append(f"Agent execution failed: {str(e)}")
            return {
                "success": False,
                "filled_fields": filled_fields,
                "failed_fields": [f.element_id for f in fields],
                "errors": errors,
            }
    
    async def fill_form_from_url(
        self,
        url: str,
        data: Dict[str, Any],
        delay_between_fields: float = 0.3,
        headless: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze a URL, get fields, and fill them
        
        Args:
            url: URL to analyze and fill
            data: Dictionary mapping field identifiers to values
            delay_between_fields: Delay between field interactions
            headless: Whether to run browser in headless mode
            
        Returns:
            Dictionary with results
        """
        from app.divselection import DivSelector
        
        # Use DivSelector to get fields
        async with DivSelector(headless=headless) as selector:
            await selector.navigate(url)
            fields = await selector.find_fields()
            
            if not fields:
                return {
                    "success": False,
                    "filled_fields": [],
                    "failed_fields": [],
                    "errors": ["No form fields found on the page"],
                }
            
            # Fill the fields
            return await self.fill_form_fields(fields, data, delay_between_fields)

