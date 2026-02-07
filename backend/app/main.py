from fastapi import FastAPI

from app.routers import health, screen_control, form_filler, fields

app = FastAPI(
    title="DF26 Backend",
    description="FastAPI backend service with MCP form filling agent",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(fields.router)
app.include_router(screen_control.router)
app.include_router(form_filler.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to DF26 Backend"}
