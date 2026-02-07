"""
MCP Agent using LangChain for form filling
"""
import time
import os
import logging
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Try newer LangChain imports (v0.1+)
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    try:
        # Try langchain_core path
        from langchain_core.agents import AgentExecutor
        from langchain.agents import create_openai_tools_agent
    except ImportError:
        try:
            # Try agent_executor module directly
            from langchain.agents.agent_executor import AgentExecutor
            from langchain.agents import create_openai_tools_agent
        except ImportError:
            # Last resort - try langchain.agents.agent
            from langchain.agents.agent import AgentExecutor
            from langchain.agents import create_openai_tools_agent

from langchain_openai import ChatOpenAI
try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
except ImportError:
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
        api_base_url: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the form filler agent
        
        Args:
            model_name: OpenAI model to use
            temperature: Model temperature
            api_base_url: Base URL for screen control API (defaults to env var or localhost:8000)
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        logger.info("=" * 80)
        logger.info("Initializing MCP ReAct Form Filler Agent")
        logger.info("=" * 80)
        
        # Get API key from parameter, env var, or None
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        logger.info(f"Model: {model_name}, Temperature: {temperature}")
        logger.info(f"OpenAI API Key: {'Set' if self.openai_api_key else 'Not set'}")
        
        # Get API base URL from parameter, env var, or default
        self.api_base_url = api_base_url or os.getenv("SCREEN_CONTROL_API_URL", "http://localhost:8000/screen-control")
        logger.info(f"Screen Control API URL: {self.api_base_url}")
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=self.openai_api_key,
        )
        
        # Get tools
        self.tools = get_screen_control_tools()
        logger.info(f"Loaded {len(self.tools)} tools: {[tool.name for tool in self.tools]}")
        
        # Update base URL for all tools
        for tool in self.tools:
            if hasattr(tool, 'base_url'):
                tool.base_url = self.api_base_url
        
        # Create prompt template with explicit ReAct principles
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert form-filling agent using ReAct (Reasoning + Acting) principles to control a user's screen and fill out web forms.

REACT PRINCIPLES - Follow this loop for each field:
1. REASONING (Think): Analyze the current state, understand what needs to be done
2. ACTING (Act): Execute the appropriate action using available tools
3. OBSERVING (Observe): Check the result of your action (screenshot, tool response)
4. REASONING (Think): Evaluate if the action succeeded, decide next steps

Your capabilities (Tools available):
- get_screen_info: Get screen dimensions and current mouse position
- take_screenshot: Take a screenshot to see the current state
- move_mouse: Move mouse cursor to coordinates
- click_mouse: Click at specific coordinates
- type_text: Type text at current cursor position
- press_key: Press keyboard keys (e.g., "ctrl+a", "delete", "enter", "tab")
- scroll: Scroll the mouse wheel
- fill_text_field: Fill a text field (clicks, clears, types)
- select_dropdown_option: Select an option from a dropdown

REACT WORKFLOW for filling forms:
IMPORTANT: Take a screenshot ONCE at the start if needed, then proceed to fill fields. Do NOT take screenshots for each field - this wastes time and tokens.

For each field, follow this pattern:

THINK: "I need to fill field '{{field_id}}' ({{field_type}}) at position ({{center_x}}, {{center_y}}) with value '{{value}}'."

ACT: 
  - For text/email/password fields:
    1. Use fill_text_field(x, y, width, height, value) - this handles click, clear, and type in one efficient call
    OR if fill_text_field is not available:
    1. Move mouse to field center (x + width/2, y + height/2)
    2. Click to focus the field
    3. Clear existing text: press_key("ctrl+a") then press_key("delete")
    4. Type the new value: type_text({{value}})
  
  - For dropdown fields:
    1. Use select_dropdown_option(x, y, width, height, option) - this handles click and selection in one call
    OR if select_dropdown_option is not available:
    1. Move mouse to field center
    2. Click to open dropdown
    3. Type the option text or use arrow keys
    4. Press enter to select
  
  - For checkbox/radio fields:
    1. Move mouse to field center
    2. Click to toggle/select

OBSERVE: After each action, check the tool response. If it indicates success, proceed immediately to the next field. If it fails, think about why and try an alternative approach.

THINK: "Did the action succeed? If yes, move to the next field immediately. If no, what went wrong and how can I fix it?"

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

IMPORTANT: Always follow the ReAct loop. Think before acting, observe the results, and reason about next steps."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        try:
            logger.info("Creating LangChain agent with OpenAI tools...")
            # Try newer LangChain API
            self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
            logger.info("✅ Agent created successfully")
            
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=30,  # Limit iterations to prevent infinite loops
                max_execution_time=300,  # 5 minute timeout
            )
            logger.info("✅ AgentExecutor created with max_iterations=30, max_execution_time=300s")
        except Exception as e:
            # If agent creation fails, we'll handle it when it's used
            logger.error(f"❌ Failed to create agent: {str(e)}", exc_info=True)
            self.agent = None
            self.agent_executor = None
            self._agent_error = str(e)
    
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
        logger.info("=" * 80)
        logger.info("STARTING FORM FILL OPERATION")
        logger.info("=" * 80)
        logger.info(f"Fields to fill: {len(fields)}")
        logger.info(f"Data provided: {list(data.keys())}")
        logger.info(f"Delay between fields: {delay_between_fields}s")
        logger.info(f"Screenshot before: {screenshot_before}, Screenshot after: {screenshot_after}")
        
        filled_fields = []
        failed_fields = []
        errors = []
        screenshot_before_data = None
        screenshot_after_data = None
        
        # Take screenshot before if requested
        if screenshot_before:
            logger.info("📸 Taking screenshot before filling...")
            try:
                screenshot_tool = next(t for t in self.tools if t.name == "take_screenshot")
                screenshot_before_data = screenshot_tool._run()
                logger.info("✅ Screenshot before taken successfully")
            except Exception as e:
                error_msg = f"Failed to take screenshot before: {str(e)}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
        
        # Build instruction for agent
        logger.info("📝 Building instruction for agent...")
        field_descriptions = []
        for i, field in enumerate(fields, 1):
            field_id = field.id
            field_type = field.field_type
            bbox = field.bounding_box
            value = data.get(field_id, "")
            label = field.label or field_id
            
            logger.info(f"  Field {i}/{len(fields)}: {field_id} ({field_type}) at ({bbox.center_x}, {bbox.center_y}) = '{value}'")
            
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
1. OPTIONAL: Take ONE screenshot at the start if you need to see the current state (but this is usually not necessary since you have field coordinates)
2. For each field, use the most efficient tool:
   - For text/email/password: Use fill_text_field(x, y, width, height, value) 
   - For dropdown: Use select_dropdown_option(x, y, width, height, option)
   - For checkbox/radio: Use click_mouse(center_x, center_y)
3. Work through fields sequentially
4. Be precise with coordinates
5. After each successful action, immediately proceed to the next field

IMPORTANT: Do NOT take screenshots for each field. Use the field coordinates directly. Only take a screenshot once at the start if absolutely necessary."""
        
        logger.info("=" * 80)
        logger.info("AGENT INPUT INSTRUCTION")
        logger.info("=" * 80)
        logger.info(f"Instruction length: {len(instruction)} characters")
        logger.info(f"Instruction preview (first 500 chars):\n{instruction[:500]}...")
        logger.info("=" * 80)
        
        try:
            if self.agent_executor is None:
                error_msg = f"Agent not initialized: {getattr(self, '_agent_error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            logger.info("🤖 Executing agent...")
            logger.info("=" * 80)
            start_time = time.time()
            
            # Execute agent
            result = self.agent_executor.invoke({
                "input": instruction,
                "chat_history": [],
            })
            
            execution_time = time.time() - start_time
            logger.info("=" * 80)
            logger.info(f"✅ Agent execution completed in {execution_time:.2f} seconds")
            logger.info("=" * 80)
            
            # Parse result
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            logger.info("=" * 80)
            logger.info("AGENT OUTPUT")
            logger.info("=" * 80)
            logger.info(f"Output length: {len(output)} characters")
            logger.info(f"Output:\n{output}")
            logger.info("=" * 80)
            
            logger.info(f"Intermediate steps: {len(intermediate_steps)}")
            for i, step in enumerate(intermediate_steps, 1):
                logger.info(f"  Step {i}: {type(step).__name__}")
                if hasattr(step, 'tool') and hasattr(step, 'tool_input'):
                    logger.info(f"    Tool: {step.tool if isinstance(step.tool, str) else getattr(step.tool, 'name', 'unknown')}")
                    logger.info(f"    Input: {step.tool_input}")
                if hasattr(step, 'log'):
                    logger.info(f"    Log: {step.log[:200]}..." if len(str(step.log)) > 200 else f"    Log: {step.log}")
            
            # Check which fields were successfully filled
            # This is a simplified check - in practice, you'd want more sophisticated verification
            logger.info("=" * 80)
            logger.info("ANALYZING RESULTS")
            logger.info("=" * 80)
            for field in fields:
                field_id = field.id
                if field_id in output.lower() or "success" in output.lower():
                    filled_fields.append(field_id)
                    logger.info(f"✅ Field '{field_id}' appears to be filled")
                else:
                    failed_fields.append(field_id)
                    logger.info(f"⚠️  Field '{field_id}' status unclear")
            
            # If we couldn't determine, assume all were attempted
            if not filled_fields and not failed_fields:
                filled_fields = [f.id for f in fields]
                logger.info("⚠️  Could not determine field status, assuming all were attempted")
            
            logger.info(f"Summary: {len(filled_fields)} filled, {len(failed_fields)} failed")
            
        except Exception as e:
            error_msg = f"Agent execution failed: {str(e)}"
            logger.error("=" * 80)
            logger.error("❌ AGENT EXECUTION ERROR")
            logger.error("=" * 80)
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            failed_fields = [f.id for f in fields]
        
        # Take screenshot after if requested
        if screenshot_after:
            logger.info("📸 Taking screenshot after filling...")
            try:
                screenshot_tool = next(t for t in self.tools if t.name == "take_screenshot")
                screenshot_after_data = screenshot_tool._run()
                logger.info("✅ Screenshot after taken successfully")
            except Exception as e:
                error_msg = f"Failed to take screenshot after: {str(e)}"
                logger.error(f"❌ {error_msg}")
                errors.append(error_msg)
        
        # Final result
        success = len(filled_fields) > 0 and len(failed_fields) == 0
        logger.info("=" * 80)
        logger.info("FINAL RESULT")
        logger.info("=" * 80)
        logger.info(f"Success: {success}")
        logger.info(f"Filled fields ({len(filled_fields)}): {filled_fields}")
        if failed_fields:
            logger.info(f"Failed fields ({len(failed_fields)}): {failed_fields}")
        if errors:
            logger.info(f"Errors ({len(errors)}): {errors}")
        logger.info("=" * 80)
        
        return FormFillResult(
            success=success,
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

