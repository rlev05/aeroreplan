from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.api import router as api_router
from backend.app.persistence import init_database


@asynccontextmanager
async def lifespan(
        app: FastAPI,
):
    init_database()

    yield

app = FastAPI(
    title="AeroReplan API",
    description=("Decision-intelligence platform for short-haul airline "
        "disruption recovery."
                 ),
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(api_router)

@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "AeroReplan API",
        "status": "running",
    }

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }

