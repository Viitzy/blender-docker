from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import lots

app = FastAPI(title="Lot Render API")

# Allow any origin with "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with prefix
app.include_router(lots.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
