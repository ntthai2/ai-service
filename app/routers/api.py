from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import PredictRequest, PredictResponse, PredictionOut
from app.models.db import Prediction
from app.services.database import SessionLocal
from app.services.core import predict_text

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    label, score = predict_text(req.text)

    record = Prediction(
        input_text=req.text,
        label=label,
        score=score
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "label": label,
        "score": score
    }


@router.get(
    "/result/{prediction_id}",
    response_model=PredictionOut
)
def get_result(prediction_id: int, db: Session = Depends(get_db)):

    result = db.query(Prediction)\
        .filter(Prediction.id == prediction_id)\
        .first()

    if not result:
        raise HTTPException(404, "Result not found")

    return result