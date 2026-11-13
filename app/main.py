import os

from contextlib import asynccontextmanager

from dotenv import load_dotenv

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models

from app.routes import router
from app.auth import verify_api_key
from app.rate_limit import RateLimitEvent


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Create database tables when application starts.
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(
    title="AI Chat Application",
    description="AI Chat Backend with PostgreSQL and FastAPI",
    version="1.0.0",
    lifespan=lifespan
)


# CORS configuration
origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5500"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# All session routes require API key authentication.
app.include_router(router)


@app.get(
    "/health",
    dependencies=[Depends(verify_api_key)]
)
def health_check():

    return {
        "status": "healthy",
        "application": "AI Chat Application"
    }

@app.get("/sessions", dependencies=[Depends(verify_api_key)])
def list_sessions():
    return {"message": "Sessions retrieved"}