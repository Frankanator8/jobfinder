# DF26 Backend

A FastAPI backend service.

## Prerequisites

- Python 3.10+

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Run

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Docs

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Project Structure

```
app/
├── main.py            # Application entry point
├── routers/           # API route handlers
│   └── health.py      # Health check endpoint
├── models/            # Database / ORM models
├── schemas/           # Pydantic request/response schemas
└── dependencies/      # Dependency injection utilities
```
