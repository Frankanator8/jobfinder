"""
Async Form Filler Agent - Uses bounding boxes from divselection.py to fill forms.
Controls mouse and keyboard directly (no HTTP API, no screenshots).
"""
import asyncio
import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
- Get screen dimensions to check if fields are visible
- Scroll the page if fields or buttons are outside the visible area
- Move the mouse cursor to specific coordinates
- Click on form fields using their bounding box center coordinates
- Type text into text fields
- Handle different field types appropriately

IMPORTANT RESTRICTIONS:
- Ctrl+A (select all) is DISABLED - you cannot use it
- Delete key is DISABLED - you cannot use it
- Triple click is DISABLED - you cannot use it
- Just click on fields and type - new text will be appended or replace existing text automatically

CRITICAL RULES - EXECUTE SEQUENTIALLY:
1. You will receive bounding boxes (x, y, width, height) for each field
2. Calculate the center of each field: center_x = x + width/2, center_y = y + height/2
3. Calculate bottom Y: bottom_y = y + height
4. Use the center coordinates to click on fields
5. ALWAYS execute ONE action at a time - wait for each tool to complete before calling the next
6. CRITICAL SCROLLING RULE - BEFORE interacting with ANY field or button:
   a. Get screen info to know screen height
   b. Check if field is FULLY visible: Top Y >= 0 AND Bottom Y <= screen height
   c. IF already fully visible: DO NOT scroll - proceed to click/type
   d. IF NOT fully visible, THEN scroll:
      - If Top Y < 0: Scroll UP (negative clicks, e.g., -5 to -10, minimum -1)
      - If Bottom Y > screen height: Scroll DOWN (positive clicks, e.g., 5 to 10, minimum 1)
   e. DO NOT use 0 clicks - that is invalid and will error
   f. After scrolling, check visibility again - repeat if still not fully visible
   g. DO NOT click or type until field is FULLY visible on screen
7. For each field, follow this EXACT sequence based on field type:
   a. Check visibility and scroll until FULLY visible (see rule 6)
   b. For TEXT/EMAIL/PHONE/TEXTAREA: Click, wait, type, wait
   c. For DROPDOWN/SELECT (CRITICAL): 
      - Click to OPEN the dropdown
      - Wait 0.2s for menu to appear
      - Type the option text (from data provided)
      - Wait 0.1s
      - Press Enter to select
   d. For CHECKBOX: Click to toggle
   e. For RADIO: Click to select
   NOTE: Do NOT try to clear text - Ctrl+A and Delete are DISABLED. Just click and type.
8. NEVER call multiple tools in rapid succession - each tool call must complete before the next
9. Fill fields ONE AT A TIME in the order provided - you MUST fill ALL fields on EVERY page
10. Start with the FIRST field and fill EVERY field listed - do not skip fields
11. Wait at least 0.5 seconds between filling different fields
12. Do NOT take screenshots - you only have bounding box information
13. The tools already have built-in delays - do NOT add extra delays, just use them sequentially
14. DO NOT attempt to use Ctrl+A, Delete key, or triple click - these are disabled and will fail
15. CRITICAL: On each new page, you MUST fill ALL fields starting from the FIRST field - match each field's LABEL to the best data

Field types you can handle:
- text, email, phone, name: Regular text input fields - click, then type (text may append or replace automatically)
- textarea: Multi-line text fields - click, then type (text may append or replace automatically)
- select, dropdown: CRITICAL - Dropdown/select fields require special handling:
  * Step 1: Click on the dropdown field to open it
  * Step 2: Wait for dropdown menu to appear (0.2 seconds)
  * Step 3: Type the option text to search/select it (the value provided in the data)
  * Step 4: Press Enter to confirm the selection
  * If typing doesn't work, try clicking on the option directly if visible
- checkbox: Checkbox fields - click to toggle (click once to check, click again to uncheck)
- radio: Radio button fields - click to select (only one can be selected in a group)
- file: File upload fields - click to open file dialog (you can't upload files, just click)
- date: Date input fields - click, then type date in format MM/DD/YYYY or YYYY-MM-DD (text may append or replace automatically)
- password: Password fields - click, then type (text will be hidden, may append or replace automatically)
- submit, button: Button fields - click to submit/continue (do NOT fill with text, just click)

You will receive:
- Field LABELS - the most important identifier for matching fields to data (e.g., "First Name", "Email", "Position")
- Field bounding boxes (x, y, width, height) - these are screen coordinates
- Field types - what kind of field it is
- Available user data - a list of all data keys and values you can use
- Button fields (submit/next buttons) - these should be clicked AFTER filling all input fields

CRITICAL MATCHING INSTRUCTIONS:
- Each field will have a LABEL (e.g., "First Name", "Email", "Position", "Experience Years")
- You MUST match each field's LABEL to the most appropriate data key from the available user data
- LABEL-BASED MATCHING IS PRIMARY: Compare the field's LABEL to data keys to find the best semantic match
- Look for semantic matches: "First Name" → "firstname" or "first name", "Email" → "email", etc.
- You MUST fill ALL fields on EVERY page - do not skip fields unless they have absolutely no matching data
- DO NOT use the same data for multiple fields on the same page - each field should get its own appropriate data
- You CAN reuse data across different pages if the field labels are the same (e.g., "Email" on page 1 and "Email" on page 2)
- If a field label doesn't match any available data after careful checking, you may skip it
- The system will suggest a match with a score (0-100), but you should verify it makes semantic sense based on the label
- Higher match scores (80-100) are very reliable, lower scores (40-60) require more careful verification

IMPORTANT: After filling all input fields, you will be instructed to click on any next/submit button if one exists. Do NOT click buttons before filling all input fields. Be precise with coordinates and methodical in your approach. Fill one field at a time."""),
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
        delay_between_fields: float = 0.1,
        current_url: Optional[str] = None,
        current_title: Optional[str] = None,
        step_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fill out form fields using the agent asynchronously
        
        Args:
            fields: List of FormField objects from divselection.py
            data: Dictionary mapping field identifiers to values
            delay_between_fields: Delay between field interactions in seconds
            current_url: Current page URL (for agent context)
            current_title: Current page title (for agent context)
            step_number: Current step number in multi-step form (for agent context)
            
        Returns:
            Dictionary with success status and details
        """
        if self.agent_executor is None:
            raise RuntimeError(f"Agent not initialized: {getattr(self, '_agent_error', 'Unknown error')}")
        
        filled_fields = []
        failed_fields = []
        errors = []
        
        # Separate input fields from button/submit fields
        input_fields = []
        next_buttons = []  # Multi-step navigation buttons
        final_submit_buttons = []  # Final submission buttons
        
        for field in fields:
            field_type = field.field_type.value
            # Check if it's a button or submit field
            if field_type in ["submit", "button"]:
                # Use the is_next_button and is_final_submit flags from divselection
                if hasattr(field, 'is_next_button') and field.is_next_button:
                    next_buttons.append(field)
                elif hasattr(field, 'is_final_submit') and field.is_final_submit:
                    final_submit_buttons.append(field)
                else:
                    # Fallback: check by label/name if flags not set
                    label_lower = (field.label or "").lower()
                    name_lower = (field.name or "").lower()
                    next_keywords = ["next", "continue", "proceed", "forward", "step"]
                    final_keywords = ["submit", "send", "apply", "finish", "complete"]
                    if any(kw in label_lower or kw in name_lower for kw in next_keywords):
                        next_buttons.append(field)
                    elif any(kw in label_lower or kw in name_lower for kw in final_keywords):
                        final_submit_buttons.append(field)
            else:
                input_fields.append(field)
        
        # Build instruction for agent - include ALL input fields with their labels
        # Let the agent decide which data matches each field based on label
        field_descriptions = []
        
        # Log all field labels for debugging
        logger.info("=" * 60)
        logger.info("FIELDS DETECTED ON CURRENT PAGE:")
        logger.info("=" * 60)
        for idx, field in enumerate(input_fields, 1):
            field_label = field.label or field.name or 'Unnamed'
            logger.info(f"Field {idx}: Label='{field_label}' | ID='{field.element_id}' | Name='{field.name}' | Type='{field.field_type.value}'")
        logger.info("=" * 60)
        
        for field in input_fields:
            field_id = field.element_id
            field_name = field.name
            field_label = field.label or field_name or 'Unnamed'
            field_label_lower = field_label.lower()
            
            bbox = field.bounding_box
            center_x = bbox.get("x", 0) + bbox.get("width", 0) // 2
            center_y = bbox.get("y", 0) + bbox.get("height", 0) // 2
            field_y = bbox.get("y", 0)
            field_height = bbox.get("height", 0)
            field_bottom_y = field_y + field_height
            
            # Find best matching data key based on label similarity
            # Priority: Label > Name > ID, with various matching strategies
            best_match_key = None
            best_match_value = None
            best_score = 0
            
            # Normalize field label for matching (remove common words, punctuation)
            field_label_normalized = field_label_lower.replace("'", "").replace("-", " ").replace("_", " ")
            field_label_words = [w for w in field_label_normalized.split() if len(w) > 2]
            
            for key, val in data.items():
                key_lower = key.lower()
                key_normalized = key_lower.replace("'", "").replace("-", " ").replace("_", " ")
                key_words = [w for w in key_normalized.split() if len(w) > 2]
                score = 0
                
                # Exact match gets highest score
                if key_lower == field_label_lower:
                    score = 100
                # Normalized exact match (ignoring punctuation/spaces)
                elif key_normalized == field_label_normalized:
                    score = 95
                # Field name match
                elif field_name and key_lower == field_name.lower():
                    score = 80
                # Field ID match
                elif key_lower == field_id.lower():
                    score = 70
                # Label contains key or key contains label (full string)
                elif key_lower in field_label_lower or field_label_lower in key_lower:
                    score = 60
                # All words from key are in label (or vice versa)
                elif len(key_words) > 0 and all(any(kw in w or w in kw for w in field_label_words) for kw in key_words):
                    score = 55
                elif len(field_label_words) > 0 and all(any(flw in w or w in flw for w in key_words) for flw in field_label_words):
                    score = 55
                # Most words match
                elif len(key_words) > 0 and len(field_label_words) > 0:
                    matching_words = sum(1 for kw in key_words if any(kw in flw or flw in kw for flw in field_label_words))
                    if matching_words >= len(key_words) * 0.7:  # 70% of words match
                        score = 50
                    elif matching_words >= len(key_words) * 0.5:  # 50% of words match
                        score = 45
                # Partial word matches (individual words)
                elif any(word in field_label_lower for word in key_words if len(word) > 3):
                    score = 40
                elif any(word in key_lower for word in field_label_words if len(word) > 3):
                    score = 40
                # Single word overlap
                elif any(kw == flw for kw in key_words for flw in field_label_words):
                    score = 35
                
                if score > best_score:
                    best_score = score
                    best_match_key = key
                    best_match_value = val
            
            # Log the match for debugging
            if best_match_key:
                logger.info(f"  ✓ Field '{field_label}' → Matched to data key '{best_match_key}' (score: {best_score})")
            else:
                logger.warning(f"  ⚠️  Field '{field_label}' → No match found in available data")
            
            # Build field description with label prominently displayed
            field_desc = (
                f"Field Label: '{field_label}'\n"
                f"  Field ID: {field_id}\n"
                f"  Field Name: {field_name or 'N/A'}\n"
                f"  Field Type: {field.field_type.value}\n"
                f"  Bounding box: x={bbox.get('x')}, y={field_y}, width={bbox.get('width')}, height={field_height}\n"
                f"  Center coordinates: ({center_x}, {center_y})\n"
                f"  Top Y coordinate: {field_y}\n"
                f"  Bottom Y coordinate: {field_bottom_y}\n"
                f"  Required: {field.required}"
            )
            
            # Add suggested value if we found a match
            if best_match_value is not None:
                field_desc += f"\n  Suggested Data Key: '{best_match_key}' (match score: {best_score})\n"
                field_desc += f"  Suggested Value: {str(best_match_value)[:100]}{'...' if len(str(best_match_value)) > 100 else ''}"
            else:
                field_desc += "\n  No automatic match found - you must choose the best data from the available options below"
            
            field_descriptions.append(field_desc)
        
        # Log buttons detected
        if next_buttons or final_submit_buttons:
            logger.info("BUTTONS DETECTED:")
            for btn in next_buttons:
                logger.info(f"  NEXT Button: Label='{btn.label or btn.name or 'Unnamed'}' | ID='{btn.element_id}'")
            for btn in final_submit_buttons:
                logger.info(f"  FINAL SUBMIT Button: Label='{btn.label or btn.name or 'Unnamed'}' | ID='{btn.element_id}'")
            logger.info("-" * 60)
        
        # Build button descriptions - prioritize next buttons, then final submit
        next_button_descriptions = []
        for button in next_buttons:
            bbox = button.bounding_box
            center_x = bbox.get("x", 0) + bbox.get("width", 0) // 2
            center_y = bbox.get("y", 0) + bbox.get("height", 0) // 2
            button_y = bbox.get("y", 0)
            button_height = bbox.get("height", 0)
            button_bottom_y = button_y + button_height
            
            next_button_descriptions.append(
                f"Next Button '{button.element_id}' ({button.label or button.name or 'Unnamed'}):\n"
                f"  Type: {button.field_type.value} (NEXT - goes to next step/page)\n"
                f"  Bounding box: x={bbox.get('x')}, y={button_y}, width={bbox.get('width')}, height={button_height}\n"
                f"  Center coordinates: ({center_x}, {center_y})\n"
                f"  Top Y coordinate: {button_y}\n"
                f"  Bottom Y coordinate: {button_bottom_y}"
            )
        
        final_submit_descriptions = []
        for button in final_submit_buttons:
            bbox = button.bounding_box
            center_x = bbox.get("x", 0) + bbox.get("width", 0) // 2
            center_y = bbox.get("y", 0) + bbox.get("height", 0) // 2
            button_y = bbox.get("y", 0)
            button_height = bbox.get("height", 0)
            button_bottom_y = button_y + button_height
            
            final_submit_descriptions.append(
                f"Final Submit Button '{button.element_id}' ({button.label or button.name or 'Unnamed'}):\n"
                f"  Type: {button.field_type.value} (FINAL SUBMIT - submits entire form)\n"
                f"  Bounding box: x={bbox.get('x')}, y={button_y}, width={bbox.get('width')}, height={button_height}\n"
                f"  Center coordinates: ({center_x}, {center_y})\n"
                f"  Top Y coordinate: {button_y}\n"
                f"  Bottom Y coordinate: {button_bottom_y}"
            )
        
        if not field_descriptions:
            return {
                "success": False,
                "filled_fields": [],
                "failed_fields": [f.element_id for f in input_fields],
                "errors": ["No input fields found on the page"],
            }
        
        # Build available data summary for agent reference
        data_summary = []
        logger.info("AVAILABLE USER DATA:")
        logger.info("-" * 60)
        for key, value in data.items():
            value_str = str(value)
            if len(value_str) > 80:
                value_str = value_str[:80] + "..."
            data_summary.append(f"  - '{key}': {value_str}")
            logger.info(f"  '{key}': {value_str}")
        logger.info("-" * 60)
        
        # Build instruction with current page context
        instruction_parts = []
        
        # Add page context information
        has_context = bool(current_url or current_title or step_number is not None)
        if has_context:
            instruction_parts.append("=" * 60)
            instruction_parts.append("CURRENT PAGE CONTEXT:")
            if step_number is not None:
                instruction_parts.append(f"  Step Number: {step_number}")
            if current_url:
                instruction_parts.append(f"  Current URL: {current_url}")
            if current_title:
                instruction_parts.append(f"  Current Page Title: {current_title}")
            instruction_parts.append("=" * 60)
            instruction_parts.append("")
            instruction_parts.append("IMPORTANT: You are now working on a NEW page. The fields below are from THIS current page.")
            instruction_parts.append("Do NOT use information from previous pages. Only use the fields listed below.")
            instruction_parts.append("")
        
        # Prepare data strings
        data_summary_str = "\n".join(data_summary)
        field_descriptions_str = "\n".join(field_descriptions)
        delay_text_field = f"   - Step 5: Wait an additional {delay_between_fields} seconds before starting the next field"
        delay_dropdown_field = f"   - Step 7: Wait an additional {delay_between_fields} seconds before starting the next field"
        
        instruction_parts.extend([
            "=" * 60,
            "TASK: FILL ALL FORM FIELDS ON THIS PAGE",
            "=" * 60,
            "",
            f"You must fill ALL {len(field_descriptions)} fields listed below on this page.",
            "Start with the FIRST field and work through them in order.",
            "Match each field's LABEL to the best data from the available user data.",
            "",
            "Fill out the following form fields on the screen using their bounding box coordinates.",
            "",
            "AVAILABLE USER DATA (choose the best match for each field based on the LABEL):",
            "",
            data_summary_str,
            "",
            "FORM FIELDS TO FILL (match each field's LABEL to the appropriate data above):",
            "",
            field_descriptions_str,
            "",
            "CRITICAL INSTRUCTIONS - EXECUTE SEQUENTIALLY:",
            "",
            "⚠️  MANDATORY: YOU MUST FILL ALL FIELDS ON THIS PAGE ⚠️",
            "- You are on a NEW page (see CURRENT PAGE CONTEXT above)",
            "- You MUST fill EVERY field listed below, starting from the FIRST field",
            "- Do NOT skip any fields unless they truly have no matching data",
            "- Fill fields in the EXACT order they are listed below",
            "- Start with the FIRST field and work through them sequentially",
            "",
            "MATCHING FIELDS TO DATA (LABEL-BASED MATCHING IS CRITICAL):",
            "- The PRIMARY way to match fields to data is by comparing the FIELD LABEL to the DATA KEY",
            "- Look at each field's LABEL (shown as 'Field Label: ...' above) - this is the MOST IMPORTANT identifier",
            "- Match the FIELD LABEL to the most semantically similar DATA KEY from 'AVAILABLE USER DATA'",
            "- Use the suggested match if provided (it shows the match score), but verify it makes semantic sense",
            "- Examples of good label-to-data matches:",
            "  * Field Label 'First Name' → Data Key 'firstname' or 'first name'",
            "  * Field Label 'Email' → Data Key 'email'",
            "  * Field Label 'Phone' → Data Key 'phone' or 'telephone'",
            "  * Field Label 'Position' → Data Key 'position' or 'job title'",
            "  * Field Label 'Years of Experience' → Data Key 'experience' or 'years'",
            "- If a field label is similar to a data key (even partially), use that data",
            "- DO NOT repeat the same data on multiple pages unless the field labels are identical",
            "- If a field label doesn't match any data semantically, you may skip it (but try hard to find a match first)",
            "- The match score (0-100) indicates confidence - higher scores are better matches",
            "",
            "0. BEFORE interacting with any field or button - CHECK VISIBILITY AND SCROLL IF NEEDED:",
            "   - Use get_screen_info tool to get screen dimensions (width x height)",
            "   - Check if the field/button is FULLY visible:",
            "     * Top Y coordinate must be >= 0 (visible at top of screen)",
            "     * Bottom Y coordinate (Top Y + Height) must be <= screen height (visible at bottom)",
            "   - IF field is ALREADY fully visible (Top Y >= 0 AND Bottom Y <= height):",
            "     * DO NOT scroll - proceed directly to clicking/typing",
            "   - IF field is NOT fully visible, THEN scroll:",
            "     * If Top Y < 0: Scroll UP (negative clicks, e.g., -5 to -10 clicks) until Top Y >= 0",
            "     * If Bottom Y > screen height: Scroll DOWN (positive clicks, e.g., 5-10 clicks) until Bottom Y <= height",
            "   - IMPORTANT: Only scroll when needed - if already visible, skip scrolling",
            "   - DO NOT use 0 clicks - that is invalid and will error",
            "   - Scroll in larger increments (5-10 clicks) if field is far off-screen",
            "   - After scrolling, check visibility again - repeat if still not fully visible",
            "   - WAIT for scrolling to complete (0.2s delay built-in) before checking again",
            "   - DO NOT proceed to click/type until field is FULLY visible on screen",
            "1. FILL ALL FIELDS - Start with the FIRST field and fill EVERY field listed below",
            "2. For EACH field (in order), follow this exact sequence based on field type:",
            "",
            "   For TEXT, EMAIL, PHONE, TEXTAREA, DATE fields:",
            "   - Step 0: Read the field's LABEL (shown in the field description above)",
            "   - Step 0.1: Find the best matching data key from 'AVAILABLE USER DATA' by comparing the LABEL to data keys",
            "   - Step 0.2: Use the suggested match if provided, or find the best semantic match yourself",
            "   - Step 0.3: Once you've identified the matching data, proceed to fill the field",
            "   - Step 0.5: Check if field is FULLY visible (use get_screen_info, scroll if needed)",
            "   - Step 1: Click on the field using center coordinates (use click_mouse tool)",
            "   - Step 2: WAIT for the click to complete (the tool handles this)",
            "   - Step 3: Type the matched value directly (use type_text tool)",
            "   - Step 4: WAIT for typing to complete",
            delay_text_field,
            "",
            "   For DROPDOWN/SELECT fields (CRITICAL - special handling required):",
            "   - Step 0: Read the field's LABEL (shown in the field description above)",
            "   - Step 0.1: Find the best matching data key from 'AVAILABLE USER DATA' by comparing the LABEL to data keys",
            "   - Step 0.2: Use the suggested match if provided, or find the best semantic match yourself",
            "   - Step 0.3: Once you've identified the matching data, proceed to fill the field",
            "   - Step 0.5: Check if field is FULLY visible (use get_screen_info, scroll if needed)",
            "   - Step 1: Click on the dropdown field to OPEN it (use click_mouse tool)",
            "   - Step 2: WAIT 0.2 seconds for the dropdown menu to appear",
            "   - Step 3: Type the matched option text to search/select it (use type_text tool)",
            "   - Step 4: WAIT 0.1 seconds after typing",
            "   - Step 5: Press Enter to confirm the selection (use press_key tool with 'enter')",
            "   - Step 6: WAIT for selection to complete",
            delay_dropdown_field,
            "",
            "   For CHECKBOX fields:",
            "   - Step 0: Check if field is FULLY visible",
            "   - Step 1: Click on the checkbox to toggle it (use click_mouse tool)",
            "   - Step 2: WAIT for the click to complete",
            "",
            "   For RADIO fields:",
            "   - Step 0: Check if field is FULLY visible",
            "   - Step 1: Click on the radio button to select it (use click_mouse tool)",
            "   - Step 2: WAIT for the click to complete",
            "",
            "CRITICAL: Do NOT attempt to clear text using Ctrl+A or Delete - these are DISABLED.",
            "For dropdowns, you MUST click to open, type the option, then press Enter.",
            "3. NEVER call multiple tools at once - each tool must complete before calling the next",
            "4. Be precise with coordinates",
            "5. The tools have built-in delays - trust them and execute sequentially",
        ])
        
        # Add button clicking instructions
        if next_button_descriptions:
            instruction_parts.extend([
                "",
                "AFTER FILLING ALL FIELDS ABOVE:",
                "6. Click on the NEXT button (if available) to go to the next step/page:",
                "",
                f"{chr(10).join(next_button_descriptions)}",
                "",
                "   - Step 0: Check if button is FULLY visible (use get_screen_info, scroll REPEATEDLY until fully visible)",
                "   - Step 0.5: Ensure button's Top Y >= 0 AND Bottom Y <= screen height before proceeding",
                "   - Step 1: Use click_mouse tool with the button's center coordinates",
                "   - Step 2: WAIT for the click to complete",
                "   - Step 3: Wait 0.5-1 seconds for the new page to load",
                "   - NOTE: After clicking next, you will receive new fields from the next page",
            ])
        
        if final_submit_descriptions:
            instruction_parts.extend([
                "",
                "7. If no NEXT button, or after all steps are complete, click FINAL SUBMIT button:",
                "",
                f"{chr(10).join(final_submit_descriptions)}",
                "",
                "   - Step 0: Check if button is FULLY visible (use get_screen_info, scroll REPEATEDLY until fully visible)",
                "   - Step 0.5: Ensure button's Top Y >= 0 AND Bottom Y <= screen height before proceeding",
                "   - Step 1: Use click_mouse tool with the button's center coordinates",
                "   - Step 2: WAIT for the click to complete",
                "   - This will FINALLY SUBMIT the entire form",
            ])
        
        instruction_parts.extend([
            "",
            "⚠️  FINAL REMINDER:",
            "- You MUST fill ALL fields listed above, starting from the FIRST field",
            "- Match each field's LABEL to the best data key from 'AVAILABLE USER DATA'",
            "- Fill fields ONE AT A TIME in the order they are listed",
            "- Complete each field fully before moving to the next",
            "- Do NOT skip fields unless they have absolutely no matching data",
            "- Start filling NOW with the FIRST field in the list above"
        ])
        
        instruction = "\n".join(instruction_parts)
        
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
        delay_between_fields: float = 0.1,
        headless: bool = True,
        max_steps: int = 10,
    ) -> Dict[str, Any]:
        """
        Analyze a URL, get fields, and fill them. Handles multi-step forms by
        re-running divselection after each "next" button click.
        
        Args:
            url: URL to analyze and fill
            data: Dictionary mapping field identifiers to values
            delay_between_fields: Delay between field interactions
            headless: Whether to run browser in headless mode
            max_steps: Maximum number of form steps to process (prevents infinite loops)
            
        Returns:
            Dictionary with results
        """
        from app.divselection import DivSelector
        
        all_filled_fields = []
        all_failed_fields = []
        all_errors = []
        step = 0
        
        async with DivSelector(headless=headless) as selector:
            initial_url = url
            logger.info(f"\n{'='*60}")
            logger.info(f"STARTING FORM FILLING PROCESS")
            logger.info(f"Initial URL: {initial_url}")
            logger.info(f"{'='*60}")
            
            await selector.navigate(url)
            initial_loaded_url = selector.page.url
            initial_title = await selector.page.title()
            initial_hash = initial_loaded_url.split('#')[1] if '#' in initial_loaded_url else None
            logger.info(f"After navigation, page URL: {initial_loaded_url}")
            logger.info(f"Page title: {initial_title}")
            logger.info(f"Hash fragment: {initial_hash or 'None'}")
            
            previous_url = initial_loaded_url  # Track URL across steps
            previous_title = initial_title
            previous_hash = initial_hash
            
            while step < max_steps:
                step += 1
                current_url = selector.page.url
                current_hash = current_url.split('#')[1] if '#' in current_url else None
                
                try:
                    current_title = await selector.page.title()
                except Exception:
                    current_title = previous_title
                
                # Check if page changed from previous step (multiple methods)
                page_changed = False
                change_methods = []
                
                if previous_url is not None:
                    # Method 1: URL change
                    if current_url != previous_url:
                        page_changed = True
                        change_methods.append("URL")
                        logger.info(f"\n{'='*60}")
                        logger.info(f"✓ PAGE CHANGED DETECTED (via URL)!")
                        logger.info(f"  Previous URL: {previous_url}")
                        logger.info(f"  New URL: {current_url}")
                        logger.info(f"{'='*60}")
                        print(f"\n✓ Page Changed (URL): {previous_url} → {current_url}")
                    
                    # Method 2: Hash fragment change
                    elif current_hash != previous_hash:
                        page_changed = True
                        change_methods.append("Hash")
                        logger.info(f"\n{'='*60}")
                        logger.info(f"✓ PAGE CHANGED DETECTED (via Hash)!")
                        logger.info(f"  Previous hash: {previous_hash or 'None'}")
                        logger.info(f"  New hash: {current_hash}")
                        logger.info(f"{'='*60}")
                        print(f"\n✓ Page Changed (Hash)")
                    
                    # Method 3: Title change
                    elif current_title != previous_title:
                        page_changed = True
                        change_methods.append("Title")
                        logger.info(f"\n{'='*60}")
                        logger.info(f"✓ PAGE CHANGED DETECTED (via Title)!")
                        logger.info(f"  Previous title: {previous_title}")
                        logger.info(f"  New title: {current_title}")
                        logger.info(f"{'='*60}")
                        print(f"\n✓ Page Changed (Title): {previous_title} → {current_title}")
                    
                    if not page_changed:
                        logger.info(f"\n{'='*60}")
                        logger.info(f"Page state unchanged (may be same page or SPA navigation)")
                        logger.info(f"  Current URL: {current_url}")
                        logger.info(f"  Current title: {current_title}")
                        logger.info(f"  Current hash: {current_hash or 'None'}")
                        logger.info(f"{'='*60}")
                else:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"INITIAL PAGE LOAD")
                    logger.info(f"  URL: {current_url}")
                    logger.info(f"  Title: {current_title}")
                    logger.info(f"  Hash: {current_hash or 'None'}")
                    logger.info(f"{'='*60}")
                
                # Update tracking variables
                previous_url = current_url
                previous_title = current_title
                previous_hash = current_hash
                
                print(f"Processing form step {step}...")
                logger.info(f"\n{'='*60}")
                logger.info(f"PROCESSING FORM STEP {step}")
                logger.info(f"Current URL: {current_url}")
                logger.info(f"{'='*60}")
                
                # IMPORTANT: Get fresh fields from current page using divselection
                # This is called on initial load and after each "next" button click
                logger.info("Running divselection.find_fields() to detect fields on current page...")
                logger.info(f"Analyzing page at URL: {current_url}")
                
                # Verify we're on the correct page before scanning
                actual_url = selector.page.url
                if actual_url != current_url:
                    logger.warning(f"⚠️  URL mismatch detected!")
                    logger.warning(f"  Expected URL: {current_url}")
                    logger.warning(f"  Actual page URL: {actual_url}")
                    logger.warning(f"  Using actual page URL for field detection")
                    current_url = actual_url  # Update to actual URL
                
                # Ensure page is ready before scanning
                try:
                    await selector.page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception as e:
                    logger.warning(f"Page load state wait timeout: {e}, proceeding anyway")
                
                # Get fresh fields from the CURRENT page
                fields = await selector.find_fields()
                logger.info(f"✓ divselection.find_fields() completed")
                logger.info(f"✓ Found {len(fields)} total fields on page {step}")
                logger.info(f"✓ URL analyzed: {current_url}")
                
                # Double-check the page URL after scanning
                post_scan_url = selector.page.url
                if post_scan_url != current_url:
                    logger.warning(f"⚠️  URL changed during field scanning!")
                    logger.warning(f"  Before scan: {current_url}")
                    logger.warning(f"  After scan: {post_scan_url}")
                    current_url = post_scan_url  # Update to latest URL
                
                # Log detailed field breakdown
                if fields:
                    input_count = sum(1 for f in fields if f.field_type.value not in ["submit", "button"])
                    button_count = sum(1 for f in fields if f.field_type.value in ["submit", "button"])
                    next_count = sum(1 for f in fields if hasattr(f, 'is_next_button') and f.is_next_button)
                    submit_count = sum(1 for f in fields if hasattr(f, 'is_final_submit') and f.is_final_submit)
                    
                    logger.info(f"  - Input fields: {input_count}")
                    logger.info(f"  - Buttons: {button_count} (Next: {next_count}, Final Submit: {submit_count})")
                else:
                    logger.warning(f"  ⚠️  No fields detected on this page!")
                
                if not fields:
                    if step == 1:
                        return {
                            "success": False,
                            "filled_fields": [],
                            "failed_fields": [],
                            "errors": ["No form fields found on the page"],
                        }
                    else:
                        # No more fields, form might be complete
                        break
                
                # Separate next buttons from final submit buttons
                next_buttons = [f for f in fields if hasattr(f, 'is_next_button') and f.is_next_button]
                final_submit_buttons = [f for f in fields if hasattr(f, 'is_final_submit') and f.is_final_submit]
                
                # Log what divselection found on this page
                logger.info(f"\n{'='*60}")
                logger.info(f"DIVSELECTION RESULTS FOR URL: {current_url}")
                logger.info(f"{'='*60}")
                logger.info(f"Total fields detected: {len(fields)}")
                logger.info(f"  - Input fields: {len(fields) - len(next_buttons) - len(final_submit_buttons)}")
                logger.info(f"  - Next buttons: {len(next_buttons)}")
                logger.info(f"  - Final submit buttons: {len(final_submit_buttons)}")
                
                if next_buttons:
                    for btn in next_buttons:
                        logger.info(f"    → Next button: '{btn.label or btn.name or 'Unnamed'}' (ID: {btn.element_id})")
                if final_submit_buttons:
                    for btn in final_submit_buttons:
                        logger.info(f"    → Final submit: '{btn.label or btn.name or 'Unnamed'}' (ID: {btn.element_id})")
                
                # Log all input field labels/types for matching
                input_fields = [f for f in fields if f.field_type.value not in ["submit", "button"]]
                if input_fields:
                    logger.info(f"\nInput fields detected on this page:")
                    for field in input_fields:
                        field_info = f"  - [{field.field_type.value}] "
                        if field.label:
                            field_info += f"Label: '{field.label}'"
                        if field.name:
                            field_info += f", Name: '{field.name}'"
                        if field.placeholder:
                            field_info += f", Placeholder: '{field.placeholder}'"
                        if not field.label and not field.name and not field.placeholder:
                            field_info += f"Unnamed field (ID: {field.element_id})"
                        logger.info(field_info)
                logger.info(f"{'='*60}")
                
                # Fill fields on current page
                logger.info(f"\n{'='*60}")
                logger.info(f"FEEDING FIELDS TO AGENT FOR PAGE: {current_url}")
                logger.info(f"Agent will now fill {len(input_fields)} input fields")
                logger.info(f"{'='*60}")
                
                # Get current page title for agent context
                try:
                    page_title = await selector.page.title()
                except Exception:
                    page_title = None
                
                # Pass current page state to agent so it knows it's on a new page
                result = await self.fill_form_fields(
                    fields, 
                    data, 
                    delay_between_fields,
                    current_url=current_url,
                    current_title=page_title,
                    step_number=step
                )
                all_filled_fields.extend(result.get("filled_fields", []))
                all_failed_fields.extend(result.get("failed_fields", []))
                all_errors.extend(result.get("errors", []))
                
                logger.info(f"\n{'='*60}")
                logger.info(f"AGENT COMPLETED FILLING FOR URL: {current_url}")
                logger.info(f"  Filled: {len(result.get('filled_fields', []))} fields")
                logger.info(f"  Failed: {len(result.get('failed_fields', []))} fields")
                logger.info(f"{'='*60}")
                
                # Check if there's a next button to click
                if next_buttons:
                    print(f"Found {len(next_buttons)} next button(s). Clicking it to proceed to next step...")
                    logger.info(f"\n{'='*60}")
                    logger.info(f"GUARANTEEING NEXT BUTTON CLICK")
                    logger.info(f"{'='*60}")
                    
                    # Store current page state before navigation (multiple detection methods)
                    previous_url = selector.page.url
                    previous_title = await selector.page.title()
                    previous_hash = selector.page.url.split('#')[1] if '#' in selector.page.url else None
                    
                    # Get initial DOM fingerprint (hash of page content)
                    try:
                        previous_dom_hash = await selector.page.evaluate("""
                            () => {
                                const body = document.body;
                                if (!body) return '';
                                // Create a simple hash of visible content
                                const text = body.innerText || body.textContent || '';
                                const formCount = document.querySelectorAll('form, input, select, textarea').length;
                                return text.substring(0, 100) + '|' + formCount;
                            }
                        """)
                    except Exception as e:
                        logger.warning(f"Could not get initial DOM hash: {e}")
                        previous_dom_hash = None
                    
                    logger.info(f"Current URL before next click: {previous_url}")
                    logger.info(f"Current title before next click: {previous_title}")
                    logger.info(f"Current hash before next click: {previous_hash or 'None'}")
                    
                    # GUARANTEE: Actually click the next button programmatically
                    import pyautogui
                    next_button = next_buttons[0]  # Use the first next button
                    bbox = next_button.bounding_box
                    center_x = bbox.get("x", 0) + bbox.get("width", 0) // 2
                    center_y = bbox.get("y", 0) + bbox.get("height", 0) // 2
                    
                    # Offset Y coordinate down a little (add 5-10 pixels)
                    offset_down = 8  # Pixels to offset downward
                    click_y = center_y + offset_down
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"CLICKING NEXT BUTTON")
                    logger.info(f"Button center: ({center_x}, {center_y})")
                    logger.info(f"Click position (offset down): ({center_x}, {click_y})")
                    logger.info(f"Button: '{next_button.label or next_button.name or 'Unnamed'}'")
                    logger.info(f"{'='*60}")
                    
                    # Ensure button is visible before clicking
                    try:
                        # Scroll if needed to make button visible
                        screen_width, screen_height = pyautogui.size()
                        button_y = bbox.get("y", 0)
                        button_height = bbox.get("height", 0)
                        button_bottom_y = button_y + button_height
                        
                        if button_y < 0 or button_bottom_y > screen_height:
                            logger.info("Button not fully visible, scrolling to make it visible...")
                            if button_y < 0:
                                # Scroll up
                                pyautogui.scroll(-5)
                            else:
                                # Scroll down
                                pyautogui.scroll(5)
                            await asyncio.sleep(0.3)
                        
                        # Move mouse to button position (offset down from center)
                        pyautogui.moveTo(center_x, click_y, duration=0.1)
                        await asyncio.sleep(0.1)
                        
                        # Click the next button at offset position
                        pyautogui.click(center_x, click_y, button='left', clicks=1)
                        logger.info(f"✓ Next button clicked at ({center_x}, {click_y}) - offset {offset_down}px down from center")
                        
                        # Wait for click to register
                        await asyncio.sleep(0.5)
                        
                        # Verify click was successful by checking if page state changed
                        try:
                            # Quick check if URL changed (indicates navigation started)
                            current_url_check = selector.page.url
                            if current_url_check != previous_url:
                                logger.info(f"✓ Click verified - URL changed: {previous_url} → {current_url_check}")
                            else:
                                logger.info(f"✓ Click executed - waiting for navigation...")
                        except Exception as e:
                            logger.warning(f"Could not verify click: {e}, proceeding anyway")
                        
                    except Exception as e:
                        logger.error(f"Error clicking next button: {e}")
                        logger.info("Attempting to continue anyway...")
                        await asyncio.sleep(0.5)
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"NEXT BUTTON CLICK CONFIRMED - PROCEEDING WITH URL WORKFLOW")
                    logger.info(f"{'='*60}")
                    
                    # NEW WORKFLOW: Copy URL from browser, paste into input stream, then rescan
                    logger.info(f"\n{'='*60}")
                    logger.info(f"URL COPY/PASTE WORKFLOW AFTER NEXT BUTTON CLICK")
                    logger.info(f"Current URL before copy: {previous_url}")
                    logger.info(f"{'='*60}")
                    
                    # Import pyautogui for direct control
                    import pyautogui
                    import platform
                    
                    try:
                        # Step 1: Move mouse to hardcoded position (410, 105) - this is where the URL is in browser
                        logger.info("Step 1: Moving mouse to fixed position (410, 105)...")
                        pyautogui.moveTo(410, 105, duration=0.1)
                        await asyncio.sleep(0.1)
                        logger.info("✓ Mouse moved to (410, 105)")
                        
                        # Step 2: Click on the browser URL bar to focus/select it
                        logger.info("Step 2: Clicking on browser URL bar to focus it...")
                        pyautogui.click(410, 105, button='left', clicks=1)
                        await asyncio.sleep(0.2)  # Wait for click to register and URL to be selected
                        logger.info("✓ Clicked on URL bar")
                        
                        # Step 3: Copy the URL (Command+C on Mac, Ctrl+C on Windows/Linux)
                        logger.info("Step 3: Copying URL to clipboard...")
                        if platform.system() == 'Darwin':  # Mac
                            pyautogui.hotkey('command', 'c')
                        else:  # Windows/Linux
                            pyautogui.hotkey('ctrl', 'c')
                        await asyncio.sleep(0.2)  # Wait for copy to complete
                        logger.info("✓ URL copied to clipboard")
                        
                        # Step 4: Tab once to move to the next available input field (Command+Tab on Mac, Ctrl+Tab on Windows/Linux)
                        logger.info("Step 4: Pressing Command+Tab (Mac) or Ctrl+Tab (Windows/Linux) to move to next input field...")
                        if platform.system() == 'Darwin':  # Mac
                            pyautogui.hotkey('command', 'tab')
                        else:  # Windows/Linux
                            pyautogui.hotkey('ctrl', 'tab')
                        await asyncio.sleep(0.3)  # Wait for focus to move to next field
                        logger.info("✓ Tabbed to next input field")
                        
                        # Step 5: Paste the URL (Command+V on Mac, Ctrl+V on Windows/Linux)
                        logger.info("Step 5: Pasting URL into input field...")
                        if platform.system() == 'Darwin':  # Mac
                            pyautogui.hotkey('command', 'v')
                        else:  # Windows/Linux
                            pyautogui.hotkey('ctrl', 'v')
                        await asyncio.sleep(0.5)  # Wait for paste and processing
                        logger.info("✓ URL pasted into input field")
                        
                        # Step 6: Tab again (Command+Tab on Mac, Ctrl+Tab on Windows/Linux) - second tab after paste
                        logger.info("Step 6: Pressing Command+Tab (Mac) or Ctrl+Tab (Windows/Linux) again after paste...")
                        if platform.system() == 'Darwin':  # Mac
                            pyautogui.hotkey('command', 'tab')
                        else:  # Windows/Linux
                            pyautogui.hotkey('ctrl', 'tab')
                        await asyncio.sleep(0.3)  # Wait for focus to move
                        logger.info("✓ Tabbed again after paste")
                        
                        logger.info(f"\n{'='*60}")
                        logger.info(f"URL COPY/PASTE WORKFLOW COMPLETE")
                        logger.info(f"STOPPING CURRENT AGENT EXECUTION")
                        logger.info(f"RESTARTING WITH FRESH divselection SCAN")
                        logger.info(f"{'='*60}")
                        
                        # Step 7: Wait briefly for the pasted URL to be processed
                        await asyncio.sleep(1.0)  # Wait for the input stream to process the URL
                        
                        # Step 8: The input stream should have navigated to the new URL
                        # Wait for page to be ready
                        try:
                            await selector.page.wait_for_load_state("domcontentloaded", timeout=5000)
                            await asyncio.sleep(0.5)  # Additional wait for dynamic content
                        except Exception as e:
                            logger.warning(f"Page load wait timeout: {e}, proceeding anyway")
                            await asyncio.sleep(0.5)
                        
                        # Get the new URL after paste/navigation
                        final_url = selector.page.url
                        try:
                            final_title = await selector.page.title()
                        except Exception:
                            final_title = previous_title
                        final_hash = final_url.split('#')[1] if '#' in final_url else None
                        
                        logger.info(f"\n{'='*60}")
                        logger.info(f"URL PROCESSING COMPLETE")
                        logger.info(f"Final URL after paste: {final_url}")
                        logger.info(f"Final title: {final_title}")
                        logger.info(f"Final hash: {final_hash or 'None'}")
                        logger.info(f"{'='*60}")
                        print(f"URL processed: {final_url} (Title: {final_title})")
                        
                    except Exception as e:
                        logger.error(f"Error in URL copy/paste workflow: {e}")
                        logger.info("Falling back to standard navigation detection...")
                        # Fallback: just get current URL
                        final_url = selector.page.url
                        try:
                            final_title = await selector.page.title()
                        except Exception:
                            final_title = previous_title
                        final_hash = final_url.split('#')[1] if '#' in final_url else None
                    
                    # CRITICAL: Immediately stop current agent execution and restart with fresh divselection scan
                    logger.info(f"\n{'='*60}")
                    logger.info(f"STOPPING CURRENT AGENT EXECUTION")
                    logger.info(f"IMMEDIATELY RE-RUNNING divselection.find_fields() ON NEW PAGE")
                    logger.info(f"URL to analyze: {final_url}")
                    logger.info(f"Restarting agent with fresh fields from new page")
                    logger.info(f"{'='*60}")
                    
                    # Update tracking variables for next iteration comparison
                    previous_url = final_url
                    previous_title = final_title
                    previous_hash = final_hash
                    
                    # Immediately rescan with divselection to get fresh fields
                    logger.info("Immediately rescanning page with divselection.find_fields()...")
                    try:
                        await selector.page.wait_for_load_state("domcontentloaded", timeout=3000)
                    except Exception:
                        pass
                    
                    # Get fresh fields immediately after paste
                    fresh_fields = await selector.find_fields()
                    logger.info(f"✓ Fresh scan complete - found {len(fresh_fields)} fields on new page")
                    
                    # Break out of current step and continue to next iteration
                    # This will restart the agent with the fresh fields from the new page
                    logger.info("Breaking out of current step to restart agent with fresh fields...")
                    continue
                
                # If there's a final submit button, the agent should have clicked it
                if final_submit_buttons:
                    print(f"Found {len(final_submit_buttons)} final submit button(s). Form submission should be complete.")
                    break
                
                # No buttons found, assume form is complete
                print("No next or submit buttons found. Assuming form is complete.")
                break
            
            if step >= max_steps:
                all_errors.append(f"Reached maximum steps ({max_steps}). Form may have more steps.")
            
            return {
                "success": len(all_filled_fields) > 0 and len(all_failed_fields) == 0,
                "filled_fields": all_filled_fields,
                "failed_fields": all_failed_fields,
                "errors": all_errors,
                "steps_processed": step,
                "output": f"Processed {step} form step(s)"
            }

