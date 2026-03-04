from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(..., max_length=500)


class PredictResponse(BaseModel):
    id: int
    label: str
    score: float


class PredictionOut(BaseModel):
    id: int
    input_text: str
    label: str
    score: float

    class Config:
        from_attributes = True