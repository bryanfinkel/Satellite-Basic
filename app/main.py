# File: app/main.py
# Path: Satellite-Basic/app/main.py
# Description: Main FastAPI application entry point

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Satellite-Basic",
    description="Satellite imagery analysis using STAC API",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router with /api/v1 prefix
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Satellite Imagery Analysis API"}