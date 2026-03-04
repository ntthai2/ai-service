from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

Base = declarative_base()


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    input_text = Column(String, nullable=False)
    label = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)