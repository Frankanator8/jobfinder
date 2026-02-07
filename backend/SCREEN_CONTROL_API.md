# Screen Control API Documentation

This API provides endpoints for controlling the user's screen and mouse. These endpoints are designed to be called by an agent to perform automated screen interactions.

## ⚠️ Security Warning

**These endpoints provide full control over the user's screen and input devices.**
- Use with extreme caution
- Implement proper authentication and authorization
- Consider rate limiting
- Only expose these endpoints in trusted environments
- Never expose these endpoints publicly without authentication

## Endpoints

### Screen Information

#### `GET /screen-control/info`
Get current screen information including size and mouse position.

**Response:**
```json
{
  "width": 1920,
  "height": 1080,
  "current_x": 500,
  "current_y": 300
}
```

### Mouse Control

#### `POST /screen-control/mouse/move`
Move the mouse cursor to a specific position.

**Request Body:**
```json
{
  "x": 500,
  "y": 300,
  "duration": 0.5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mouse moved to (500, 300)",
  "current_position": "(500, 300)"
}
```

#### `POST /screen-control/mouse/click`
Perform a mouse click at a specific position or current position.

**Request Body:**
```json
{
  "x": 500,
  "y": 300,
  "button": "left",
  "clicks": 1,
  "interval": null
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mouse left clicked 1 time(s)"
}
```

#### `POST /screen-control/mouse/drag`
Drag the mouse from one position to another.

**Request Body:**
```json
{
  "start_x": 100,
  "start_y": 100,
  "end_x": 500,
  "end_y": 500,
  "duration": 0.5,
  "button": "left"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mouse dragged from (100, 100) to (500, 500)"
}
```

#### `POST /screen-control/mouse/scroll`
Scroll the mouse wheel at a specific position or current position.

**Request Body:**
```json
{
  "x": 500,
  "y": 300,
  "clicks": 3,
  "horizontal": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Scrolled 3 clicks vertically"
}
```

#### `GET /screen-control/mouse/position`
Get the current mouse cursor position.

**Response:**
```json
{
  "x": 500,
  "y": 300
}
```

### Keyboard Control

#### `POST /screen-control/keyboard/press`
Press keyboard key(s). Supports key combinations.

**Request Body:**
```json
{
  "keys": "ctrl+c",
  "presses": 1,
  "interval": null
}
```

**Common key combinations:**
- `ctrl+c` - Copy
- `ctrl+v` - Paste
- `ctrl+a` - Select all
- `ctrl+z` - Undo
- `ctrl+s` - Save
- `enter` - Enter key
- `tab` - Tab key
- `escape` - Escape key
- `shift+tab` - Shift+Tab

**Response:**
```json
{
  "status": "success",
  "message": "Pressed 'ctrl+c' 1 time(s)"
}
```

#### `POST /screen-control/keyboard/type`
Type text at the current cursor position.

**Query Parameters:**
- `text` (required): Text to type
- `interval` (optional): Delay between keystrokes in seconds

**Example:**
```
POST /screen-control/keyboard/type?text=Hello%20World&interval=0.1
```

**Response:**
```json
{
  "status": "success",
  "message": "Typed text: Hello World"
}
```

### Screenshots

#### `GET /screen-control/screenshot`
Take a screenshot of the screen or a specific region.

**Query Parameters:**
- `region` (optional): Region in format "x,y,width,height" (e.g., "100,100,800,600")
- `format` (optional): Image format (png, jpg, jpeg) - default: png

**Example:**
```
GET /screen-control/screenshot?region=100,100,800,600&format=png
```

**Response:** Image file (PNG/JPEG)

#### `GET /screen-control/screenshot/base64`
Take a screenshot and return it as a base64-encoded string.

**Query Parameters:**
- `region` (optional): Region in format "x,y,width,height"

**Response:**
```json
{
  "status": "success",
  "image": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "format": "png"
}
```

## Usage Examples

### Example 1: Click a button at specific coordinates
```bash
curl -X POST http://localhost:8000/screen-control/mouse/click \
  -H "Content-Type: application/json" \
  -d '{"x": 500, "y": 300, "button": "left", "clicks": 1}'
```

### Example 2: Drag and drop
```bash
curl -X POST http://localhost:8000/screen-control/mouse/drag \
  -H "Content-Type: application/json" \
  -d '{
    "start_x": 100,
    "start_y": 100,
    "end_x": 500,
    "end_y": 500,
    "duration": 0.5,
    "button": "left"
  }'
```

### Example 3: Take a screenshot
```bash
curl -X GET http://localhost:8000/screen-control/screenshot > screenshot.png
```

### Example 4: Type text
```bash
curl -X POST "http://localhost:8000/screen-control/keyboard/type?text=Hello%20World"
```

### Example 5: Copy text (Ctrl+C)
```bash
curl -X POST http://localhost:8000/screen-control/keyboard/press \
  -H "Content-Type: application/json" \
  -d '{"keys": "ctrl+c", "presses": 1}'
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200 OK` - Success
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Server error

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Platform Support

The API uses `pyautogui` which supports:
- Windows
- macOS
- Linux (X11)

Note: On Linux, you may need to install additional dependencies:
```bash
sudo apt-get install python3-tk python3-dev
```

## Agent Integration

These endpoints are designed to be called by an agent. The agent can:
1. Get screen information to understand the display
2. Take screenshots to see what's on screen
3. Move the mouse and click to interact with UI elements
4. Type text and press keys to input data
5. Scroll to navigate content

Example agent workflow:
1. Take screenshot to see current state
2. Analyze screenshot (using vision model)
3. Determine action needed
4. Call appropriate endpoint (move, click, type, etc.)
5. Verify result with another screenshot

