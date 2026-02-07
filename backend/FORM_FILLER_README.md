# Form Filler Agent (MCP with LangChain)

An MCP (Model Context Protocol) agent built with LangChain that can automatically fill out web forms by controlling the user's screen.

## Overview

The form filler agent:
- Uses LangChain to create an intelligent agent
- Calls screen control API endpoints to interact with the screen
- Takes bounding boxes and field types as input
- Chains actions to fill out forms automatically
- Supports text fields, dropdowns, checkboxes, buttons, and more

## Architecture

```
┌─────────────────┐
│   FastAPI       │
│   Endpoints     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Form Filler    │
│  Agent          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  LangChain      │─────▶│  Screen Control   │
│  Tools          │      │  API              │
└─────────────────┘      └──────────────────┘
```

## Setup

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set OpenAI API key:**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

3. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### `POST /form-filler/fill`

Fill out form fields using the full schema.

**Request Body:**
```json
{
  "fields": [
    {
      "id": "email",
      "field_type": "email",
      "bounding_box": {
        "x": 500,
        "y": 300,
        "width": 250,
        "height": 35
      },
      "label": "Email Address",
      "required": true
    },
    {
      "id": "country",
      "field_type": "dropdown",
      "bounding_box": {
        "x": 500,
        "y": 350,
        "width": 250,
        "height": 35
      },
      "label": "Country",
      "options": ["USA", "Canada", "UK"],
      "required": true
    }
  ],
  "data": {
    "email": "user@example.com",
    "country": "USA"
  },
  "screenshot_before": true,
  "screenshot_after": true,
  "delay_between_fields": 0.5
}
```

**Response:**
```json
{
  "success": true,
  "filled_fields": ["email", "country"],
  "failed_fields": [],
  "errors": [],
  "screenshot_before": "data:image/png;base64,...",
  "screenshot_after": "data:image/png;base64,..."
}
```

### `POST /form-filler/fill-simple`

Simplified endpoint that accepts simple dictionaries.

**Request Body:**
```json
{
  "fields": [
    {
      "id": "username",
      "field_type": "text",
      "x": 500,
      "y": 300,
      "width": 200,
      "height": 30,
      "label": "Username"
    }
  ],
  "data": {
    "username": "testuser"
  },
  "delay": 0.5
}
```

## Field Types Supported

- `text` - Regular text input
- `textarea` - Multi-line text
- `dropdown` - Dropdown/select field
- `checkbox` - Checkbox
- `radio` - Radio button
- `button` - Button to click
- `date` - Date input
- `number` - Number input
- `email` - Email input
- `password` - Password input
- `file` - File upload
- `unknown` - Unknown field type

## How It Works

1. **Receive Request**: Agent receives form fields with bounding boxes and data to fill
2. **Take Screenshot**: Agent takes a screenshot to see current state
3. **Plan Actions**: Agent uses LLM to plan the sequence of actions
4. **Execute Actions**: Agent chains together:
   - Move mouse to field center
   - Click to focus field
   - Type text or select option
   - Move to next field
5. **Verify**: Agent can take screenshot after to verify

## Example Usage

### Python Script

```python
import requests

response = requests.post(
    "http://localhost:8000/form-filler/fill-simple",
    json={
        "fields": [
            {
                "id": "email",
                "field_type": "email",
                "x": 500,
                "y": 300,
                "width": 250,
                "height": 35,
                "label": "Email"
            }
        ],
        "data": {
            "email": "test@example.com"
        },
        "delay": 0.5
    }
)

print(response.json())
```

### Using Test Script

```bash
python test_form_filler.py
```

## Getting Bounding Boxes

The bounding boxes need to be provided. You can get them from:

1. **Browser DevTools**: Inspect element and get coordinates
2. **Screen capture tools**: Use tools that show coordinates
3. **Vision model**: Use a vision model to detect form fields (future enhancement)
4. **Browser extension**: Create an extension to capture field positions

Example workflow:
1. Open form in browser
2. Use DevTools to inspect a field
3. Get the element's bounding box
4. Convert to screen coordinates (accounting for browser window position)
5. Provide to API

## Agent Capabilities

The agent can:
- ✅ Take screenshots to see current state
- ✅ Move mouse cursor precisely
- ✅ Click on fields to focus them
- ✅ Type text into text fields
- ✅ Clear existing text (Ctrl+A, Delete)
- ✅ Select dropdown options
- ✅ Click checkboxes and radio buttons
- ✅ Click buttons
- ✅ Chain multiple actions together
- ✅ Wait between actions
- ✅ Handle errors gracefully

## Configuration

You can configure the agent when creating it:

```python
from app.agents.form_filler_agent import FormFillerAgent

agent = FormFillerAgent(
    model_name="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
    temperature=0.0,  # Lower = more deterministic
    api_base_url="http://localhost:8000/screen-control",
    openai_api_key="your-key"  # or set env var
)
```

## Troubleshooting

**Agent not working:**
- Check OpenAI API key is set
- Verify server is running
- Check screen control API is accessible

**Fields not being filled:**
- Verify bounding box coordinates are correct
- Make sure form is visible on screen
- Check field types match actual field types
- Increase delay between fields

**Mouse not moving:**
- Check screen control API is working
- Verify coordinates are within screen bounds
- Check for permission issues (macOS may need accessibility permissions)

## Future Enhancements

- [ ] Automatic field detection using vision models
- [ ] Support for more field types
- [ ] Better error recovery
- [ ] Field validation
- [ ] Multi-step forms
- [ ] Form state tracking
- [ ] Screenshot-based verification

## Security

⚠️ **Warning**: This agent has full control over your screen and input devices. Only use in trusted environments with proper authentication.

