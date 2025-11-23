from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from database.models import Base, Detection
from config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


router = APIRouter()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


@router.get("/", response_model=list[DetectionResponse])
def get_detections(db: Session = Depends(get_db)):
    return db.query(Detection).all()
