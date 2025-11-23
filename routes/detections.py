from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Detection
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/detections", tags=["detections"])


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

@router.get("/", response_model=List[DetectionResponse])
def get_detections(db: Session = Depends(get_db)):
    return db.query(Detection).all()
    return db.query(Detection).all()
