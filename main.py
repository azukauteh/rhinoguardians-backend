from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routes.detections import router as detections_router
from routes.notifications import router as notifications_router
from routes.alerts import router as alerts_router
from routes.api import router as api_router

"""
This is the main FastAPI application module that sets up the API server
and includes all route handlers. The API provides endpoints for rhino detection,
alerts, and system health monitoring.
"""

app = FastAPI(
    title="RhinoGuardians API",
    description="API for rhino detection and alert system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rhinoguardians-frontend-william.vercel.app/"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(alerts_router)
app.include_router(notifications_router)
app.include_router(detections_router)


@app.get("/")
def read_root():
    """
    Root endpoint that returns a welcome message.

    Returns:
        dict: A welcome message dictionary
    """
    return {"message": "Welcome to RhinoGuardians API"}


class DetectionResponse(BaseModel):
    id: int
    species: str
    confidence: float
    image_path: str
    lat: float
    lng: float
    timestamp: str

    class Config:
        orm_mode = True
