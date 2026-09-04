from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

