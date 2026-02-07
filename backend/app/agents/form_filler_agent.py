"""
MCP Agent using LangChain for form filling
"""
import time
from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.tools.screen_control_tools import get_screen_control_tools
from app.schemas.form_fields import FormField, FormFieldsRequest, FormFillResult, BoundingBox


class FormFillerAgent:
    """Agent that fills out form fields on a website"""
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
        api_base_url: str = "http://localhost:8000/screen-control",
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the form filler agent
        
        Args:
            model_name: OpenAI model to use
            temperature: Model temperature
            api_base_url: Base URL for screen control API
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.api_base_url = api_base_url
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openai_api_key,
        )
        
        # Get tools
        self.tools = get_screen_control_tools()
        # Update base URL for all tools
        for tool in self.tools:
            if hasattr(tool, 'base_url'):
                tool.base_url = api_base_url
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert form-filling agent that can control a user's screen and fill out web forms.

Your capabilities:
- Move the mouse cursor
- Click on fields
- Type text into text fields
- Select options from dropdowns
- Take screenshots to see the current state
- Scroll the page if needed

When filling out forms:
1. Always take a screenshot first to see the current state
2. Click on each field to focus it
3. For text fields: Clear existing text (Ctrl+A, Delete) then type new text
4. For dropdowns: Click to open, then type the option or use arrow keys
5. For checkboxes/radio buttons: Click on them
6. Wait a moment between actions (0.5 seconds is usually good)

Field types you can handle:
- text: Regular text input fields
- textarea: Multi-line text fields
- dropdown: Dropdown/select fields
- checkbox: Checkbox fields
- radio: Radio button fields
- button: Buttons to click
- date: Date input fields
- number: Number input fields
- email: Email input fields
- password: Password input fields

You will receive:
- Field bounding boxes (x, y, width, height) - these are the coordinates on screen
- Field types - what kind of field it is
- Data to fill - the values to put in each field

Calculate the center of each field: center_x = x + width/2, center_y = y + height/2
Use these center coordinates to click on fields.

Be careful and precise. Always verify your actions worked correctly."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )
    
    def fill_form_fields(
        self,
        fields: List[FormField],
        data: Dict[str, Any],
        delay_between_fields: float = 0.5,
        screenshot_before: bool = False,
        screenshot_after: bool = False,
    ) -> FormFillResult:
        """
        Fill out form fields using the agent
        
        Args:
            fields: List of form fields to fill
            data: Dictionary mapping field IDs to values
            delay_between_fields: Delay between field interactions
            screenshot_before: Take screenshot before filling
            screenshot_after: Take screenshot after filling
            
        Returns:
            FormFillResult with success status and details
        """
        filled_fields = []
        failed_fields = []
        errors = []
        screenshot_before_data = None
        screenshot_after_data = None
        
        # Take screenshot before if requested
        if screenshot_before:
            try:
                screenshot_tool = next(t for t in self.tools if t.name == "take_screenshot")
                screenshot_before_data = screenshot_tool._run()
            except Exception as e:
                errors.append(f"Failed to take screenshot before: {str(e)}")
        
        # Build instruction for agent
        field_descriptions = []
        for field in fields:
            field_id = field.id
            field_type = field.field_type
            bbox = field.bounding_box
            value = data.get(field_id, "")
            label = field.label or field_id
            
            field_descriptions.append(
                f"Field '{field_id}' ({label}):\n"
                f"  Type: {field_type}\n"
                f"  Position: x={bbox.x}, y={bbox.y}, width={bbox.width}, height={bbox.height}\n"
                f"  Center: ({bbox.center_x}, {bbox.center_y})\n"
                f"  Value to fill: {value}\n"
                f"  Required: {field.required}"
            )
        
        instruction = f"""Fill out the following form fields on the screen:

{chr(10).join(field_descriptions)}

Instructions:
1. Take a screenshot first to see the current state
2. For each field, click on it (use the center coordinates)
3. Fill in the value provided
4. Wait {delay_between_fields} seconds between fields
5. Be precise with coordinates

Start by taking a screenshot to see what's on the screen."""
        
        try:
            # Execute agent
            result = self.agent_executor.invoke({
                "input": instruction,
                "chat_history": [],
            })
            
            # Parse result
            output = result.get("output", "")
            
            # Check which fields were successfully filled
            # This is a simplified check - in practice, you'd want more sophisticated verification
            for field in fields:
                field_id = field.id
                if field_id in output.lower() or "success" in output.lower():
                    filled_fields.append(field_id)
                else:
                    failed_fields.append(field_id)
            
            # If we couldn't determine, assume all were attempted
            if not filled_fields and not failed_fields:
                filled_fields = [f.id for f in fields]
            
        except Exception as e:
            errors.append(f"Agent execution failed: {str(e)}")
            failed_fields = [f.id for f in fields]
        
        # Take screenshot after if requested
        if screenshot_after:
            try:
                screenshot_tool = next(t for t in self.tools if t.name == "take_screenshot")
                screenshot_after_data = screenshot_tool._run()
            except Exception as e:
                errors.append(f"Failed to take screenshot after: {str(e)}")
        
        return FormFillResult(
            success=len(filled_fields) > 0 and len(failed_fields) == 0,
            filled_fields=filled_fields,
            failed_fields=failed_fields,
            errors=errors,
            screenshot_before=screenshot_before_data,
            screenshot_after=screenshot_after_data,
        )
    
    def fill_form_from_request(self, request: FormFieldsRequest) -> FormFillResult:
        """
        Fill form from a FormFieldsRequest
        
        Args:
            request: FormFieldsRequest with fields and data
            
        Returns:
            FormFillResult
        """
        return self.fill_form_fields(
            fields=request.fields,
            data=request.data,
            delay_between_fields=request.delay_between_fields,
            screenshot_before=request.screenshot_before,
            screenshot_after=request.screenshot_after,
        )

