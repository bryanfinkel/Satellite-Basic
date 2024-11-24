# File: app/schemas/vegetation_schemas.py
# Path: Satellite-Basic/app/schemas/vegetation_schemas.py
# Description: Schemas for vegetation analysis endpoints

from typing import List, Union
from pydantic import BaseModel, field_validator
from datetime import date

class Geometry(BaseModel):
    type: str
    coordinates: List[List[List[Union[float, int]]]]

    @field_validator("type")
    def check_type(cls, v):
        if v not in ["Polygon", "MultiPolygon"]:
            raise ValueError("Type must be Polygon or MultiPolygon")
        return v

class DateRange(BaseModel):
    start_date: str
    end_date: str

class VegetationAnalysisRequest(BaseModel):
    name: str
    geometry: Geometry
    date_range: DateRange