# File: app/models/vegetation.py
# Path: Satellite-Basic/app/models/vegetation.py
# Description: Database models for vegetation analysis

from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from geoalchemy2 import Geometry
from datetime import datetime
from app.core.database import Base

class NDVIAnalysis(Base):
    __tablename__ = "ndvi_analyses"

    id = Column(String, primary_key=True)  # Changed from Integer to String
    name = Column(String, nullable=False)
    bbox = Column(ARRAY(Float))
    geometry = Column(Geometry('POLYGON', srid=4326))  # Added SRID
    ndvi_stats = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    red_url = Column(String)
    nir_url = Column(String)