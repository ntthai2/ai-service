from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import create_engine, text
from app.models.db import Base
from app.services.database import engine
from app.routers.api import router
from app.services.core import load_model

Base.metadata.create_all(bind=engine)

app = FastAPI()

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def startup_event():
    load_model()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "database": str(e)
        }