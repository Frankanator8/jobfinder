# MCP ReAct Agent for Form Filling

This document describes the MCP (Model Context Protocol) agent that uses ReAct (Reasoning + Acting) principles to automatically fill web forms by controlling the screen.

## Overview

The MCP ReAct Agent:
- **Analyzes** form fields using div selection analysis
- **Extracts** bounding boxes from detected fields
- **Uses ReAct principles** to reason about and fill forms
- **Controls the screen** via API tools to interact with form fields

## ReAct Principles

The agent follows the ReAct (Reasoning + Acting) loop:

1. **REASONING (Think)**: Analyze the current state, understand what needs to be done
2. **ACTING (Act)**: Execute the appropriate action using available tools
3. **OBSERVING (Observe)**: Check the result of your action (screenshot, tool response)
4. **REASONING (Think)**: Evaluate if the action succeeded, decide next steps

### Example ReAct Loop

```
THINK: "I need to fill field 'email' (email type) at position (500, 300) with value 'user@example.com'."

ACT: 
  - Take screenshot to observe current state
  - Move mouse to field center (500, 300)
  - Click to focus the field
  - Clear existing text: press_key("ctrl+a") then press_key("delete")
  - Type the new value: type_text("user@example.com")
  - Wait briefly (0.5 seconds)

OBSERVE: Check tool response - "Successfully filled text field"

THINK: "The email field was filled successfully. Next, I need to fill the name field."
```

## Architecture

```
┌─────────────────────┐
│  Div Selection       │
│  Analysis            │
│  (analyze_url)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Extract Bounding   │
│  Boxes              │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  MCP ReAct Agent    │
│  (FormFillerAgent)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌──────────────────┐
│  LangChain Tools     │─────▶│  Screen Control   │
│  (ReAct Loop)        │      │  API              │
└─────────────────────┘      └──────────────────┘
```

## Components

### 1. FormFillerAgent (`app/agents/form_filler_agent.py`)

The main agent class that:
- Uses LangChain's `create_openai_tools_agent` (implements ReAct)
- Has access to screen control tools
- Follows explicit ReAct principles in its prompt
- Processes form fields with bounding boxes

### 2. Screen Control Tools (`app/agents/tools/screen_control_tools.py`)

Tools available to the agent:
- `get_screen_info`: Get screen dimensions and mouse position
- `take_screenshot`: Take a screenshot to observe current state
- `move_mouse`: Move mouse cursor to coordinates
- `click_mouse`: Click at specific coordinates
- `type_text`: Type text at current cursor position
- `press_key`: Press keyboard keys (e.g., "ctrl+a", "delete", "enter")
- `scroll`: Scroll the mouse wheel
- `fill_text_field`: Fill a text field (clicks, clears, types)
- `select_dropdown_option`: Select an option from a dropdown

### 3. Auto-Fill Router (`app/routers/auto_fill.py`)

API endpoints that orchestrate the full pipeline:
- `POST /auto-fill/analyze-and-fill`: Analyze URL and fill form in one step
- `POST /auto-fill/from-analysis`: Fill form using pre-analyzed data

## Usage

### Method 1: Full Pipeline (Recommended)

Use the `/auto-fill/analyze-and-fill` endpoint:

```python
import requests

response = requests.post(
    "http://localhost:8000/auto-fill/analyze-and-fill",
    json={
        "url": "http://localhost:6767",
        "data": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-1234"
        },
        "headless": False,
        "screenshot_before": True,
        "screenshot_after": True,
        "delay_between_fields": 0.5
    }
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Filled fields: {result['fill_result']['filled_fields']}")
```

### Method 2: Two-Step Process

Step 1: Analyze the form
```python
response = requests.post(
    "http://localhost:8000/fields/analyze",
    json={"url": "http://localhost:6767", "headless": False}
)
analysis = response.json()
```

Step 2: Fill using the analysis
```python
response = requests.post(
    "http://localhost:8000/auto-fill/from-analysis",
    json={
        "analysis_result": analysis,
        "data": {"name": "John Doe", "email": "john@example.com"},
        "screenshot_before": True,
        "screenshot_after": True,
        "delay": 0.5
    }
)
result = response.json()
```

### Method 3: Direct Field Input

If you already have field definitions with bounding boxes:

```python
response = requests.post(
    "http://localhost:8000/form-filler/fill",
    json={
        "fields": [
            {
                "id": "email",
                "field_type": "email",
                "bounding_box": {"x": 500, "y": 300, "width": 250, "height": 35},
                "label": "Email Address"
            }
        ],
        "data": {"email": "user@example.com"},
        "screenshot_before": True,
        "screenshot_after": True,
        "delay_between_fields": 0.5
    }
)
```

## Testing

### Comprehensive Test Script

Run the full pipeline test:

```bash
cd backend
python test_mcp_react_agent.py
```

This test script provides three options:
1. **Full pipeline**: Analyze URL + Fill with MCP ReAct agent (recommended)
2. **Direct test**: Fill form with provided field definitions
3. **Two-step**: Analyze first, then fill separately

### Test Requirements

1. **FastAPI server running**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **OpenAI API key set**:
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Form visible on screen** (for screen control tests)

4. **URL with a form** (default: `http://localhost:6767`)

### Example Test Run

```bash
$ python test_mcp_react_agent.py

======================================================================
MCP ReAct Agent Test Suite
======================================================================

Choose test:
1. Full pipeline: Analyze URL + Fill with MCP ReAct agent (recommended)
2. Direct test: Fill form with provided field definitions
3. Two-step: Analyze first, then fill separately

Enter choice (1, 2, or 3): 1

Enter URL to test (default: http://localhost:6767): 

Enter data to fill (key=value format, one per line, empty line to finish):
  > name=John Doe
  > email=john.doe@example.com
  > phone=555-1234
  > 

Using default data: {'name': 'John Doe', 'email': 'john.doe@example.com', 'phone': '555-1234'}

======================================================================
STEP 1: Analyzing form fields using div selection
======================================================================
🌐 Analyzing URL: http://localhost:6767
✅ Analysis complete!
   Fields detected: 5

📋 Detected fields:
   1. Name (text)
      Bounding box: x=500, y=250, width=250, height=35
      Center: (625, 267)
   2. Email (email)
      Bounding box: x=500, y=300, width=250, height=35
      Center: (625, 317)
   ...

======================================================================
STEP 2: Using MCP ReAct Agent to fill form
======================================================================
📝 Data to fill: {
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "555-1234"
}

🤖 Agent will follow ReAct principles:
   - REASONING: Analyze each field and plan actions
   - ACTING: Use screen control tools to interact
   - OBSERVING: Check results after each action
   - REASONING: Decide next steps based on observations

======================================================================
STEP 3: Results
======================================================================

✅ Overall Success: True
📝 Message: Form analyzed and filled successfully

📊 Fill Results:
   Success: True
   Filled fields: ['name', 'email', 'phone']
   📸 Screenshot before: Available (base64)
   📸 Screenshot after: Available (base64)

✅✅✅ SUCCESS: Form was analyzed and filled successfully!
```

## How ReAct Works in This Agent

The agent uses LangChain's `create_openai_tools_agent`, which implements ReAct automatically. The agent:

1. **Receives a task**: "Fill these form fields with this data"

2. **Reasons**: "I need to fill field X at position Y with value Z"

3. **Acts**: Calls appropriate tools:
   - `take_screenshot` to observe current state
   - `move_mouse` to position cursor
   - `click_mouse` to focus field
   - `press_key` to clear text
   - `type_text` to enter value

4. **Observes**: Receives tool responses indicating success/failure

5. **Reasons again**: "Did that work? What's next?"

6. **Repeats** for each field

The prompt explicitly instructs the agent to follow this ReAct loop, making the reasoning process transparent and reliable.

## Field Types Supported

- `text`: Regular text input fields
- `textarea`: Multi-line text fields
- `dropdown`: Dropdown/select fields
- `checkbox`: Checkbox fields
- `radio`: Radio button fields
- `button`: Buttons to click
- `date`: Date input fields
- `number`: Number input fields
- `email`: Email input fields
- `password`: Password input fields

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required - OpenAI API key for the agent
- `SCREEN_CONTROL_API_URL`: Optional - Base URL for screen control API (default: `http://localhost:8000/screen-control`)
- `PORT`: Optional - Server port (default: `8000`)

### Agent Parameters

When creating `FormFillerAgent`:
- `model_name`: OpenAI model to use (default: `"gpt-4o-mini"`)
- `temperature`: Model temperature (default: `0.0`)
- `api_base_url`: Screen control API base URL
- `openai_api_key`: OpenAI API key

## Troubleshooting

### Agent not initializing

Check that:
- `OPENAI_API_KEY` is set
- LangChain dependencies are installed: `pip install langchain langchain-openai`
- Server is running

### Fields not being filled

- Verify bounding boxes are correct (check analysis results)
- Ensure form is visible on screen
- Check that screen control API is accessible
- Review agent logs for reasoning steps

### Tool errors

- Verify screen control API is running
- Check API base URL configuration
- Ensure screen control permissions are granted (macOS/Linux)

## Security Considerations

⚠️ **WARNING**: This agent has full control over your screen and input devices.

- Only use in trusted environments
- Implement proper authentication
- Consider rate limiting
- Never expose endpoints publicly without authentication
- Test carefully before using in production

## References

- [ReAct Paper](https://arxiv.org/abs/2210.03629): "ReAct: Synergizing Reasoning and Acting in Language Models"
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/): LangChain agent documentation
- [Model Context Protocol](https://modelcontextprotocol.io/): MCP specification

