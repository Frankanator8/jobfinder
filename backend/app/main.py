from fastapi import FastAPI

from app.routers import health

app = FastAPI(
    title="DF26 Backend",
    description="FastAPI backend service",
    version="0.1.0",
)

app.include_router(health.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to DF26 Backend"}
