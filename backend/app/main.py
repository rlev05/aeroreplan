from fastapi import FastAPI


app = FastAPI(
    title="AeroReplan API",
    description=("Decision-intelligence platform for short-haul airline "
        "disruption recovery."
                 ),
    version="0.1.0",
)

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

