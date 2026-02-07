# Environment Variables Setup

## Quick Start

1. **Copy the example file:**
   ```bash
   cd backend
   cp .env.example .env
   ```

2. **Edit `.env` and add your OpenAI API key:**
   ```bash
   # Open .env in your editor
   nano .env
   # or
   code .env
   ```

3. **Add your API key:**
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

## Environment Variables

### Required

- `OPENAI_API_KEY` - Your OpenAI API key (required for form filler agent)

### Optional

- `PORT` - Server port (default: 8000)
- `HOST` - Server host (default: 127.0.0.1)
- `SCREEN_CONTROL_API_URL` - Screen control API base URL (default: http://localhost:8000/screen-control)

## Usage

The code automatically loads environment variables from `.env` using `python-dotenv`. You don't need to manually export them.

### In Code

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Loads .env file

api_key = os.getenv("OPENAI_API_KEY")
```

### In Shell

If you prefer to use environment variables directly:

```bash
export OPENAI_API_KEY="sk-your-key-here"
uvicorn app.main:app --reload
```

## Security

⚠️ **Important:**
- `.env` is already in `.gitignore` - it won't be committed to git
- Never commit your `.env` file
- Use `.env.example` as a template for others
- Keep your API keys secret

## Verify Setup

Check if your API key is loaded:

```python
import os
from dotenv import load_dotenv

load_dotenv()
print("API Key loaded:", "Yes" if os.getenv("OPENAI_API_KEY") else "No")
```

Or test the form filler endpoint - it will show an error if the API key is missing.

