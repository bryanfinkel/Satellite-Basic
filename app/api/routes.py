# File: app/api/routes.py
# Path: Satellite-Basic/app/api/routes.py
# Description: API routes for satellite analysis services

from fastapi import APIRouter, HTTPException
from app.services.vegetation_analysis import VegetationAnalysis
from app.schemas.vegetation_schemas import VegetationAnalysisRequest
from app.core.stac_client import STACClient
from typing import List, Dict, Union

router = APIRouter()
vegetation_service = VegetationAnalysis()
stac_client = STACClient()

@router.get("/search")
async def search_images(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    start_date: str,
    end_date: str
):
    """Search for satellite images in a given area and time range"""
    try:
        bbox = [min_lon, min_lat, max_lon, max_lat]
        results = await stac_client.search_images(
            bbox=bbox,
            date_range=(start_date, end_date)
        )
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vegetation/ndvi")
async def analyze_vegetation(request: VegetationAnalysisRequest):
    """Analyze vegetation using NDVI"""
    try:
        # Get bounding box from geometry
        coords = request.geometry.coordinates[0]
        bbox = [
            min(x[0] for x in coords),  # min_lon
            min(x[1] for x in coords),  # min_lat
            max(x[0] for x in coords),  # max_lon
            max(x[1] for x in coords)   # max_lat
        ]

        # Search for images
        items = await stac_client.search_images(
            bbox=bbox,
            date_range=(request.date_range.start_date, request.date_range.end_date)
        )

        # Process NDVI using vegetation service
        ndvi_result = await vegetation_service.compute_ndvi(
            items['items'][0]['assets']['red']['href'],
            items['items'][0]['assets']['nir']['href']
        )

        # Compute statistics
        stats = await vegetation_service.compute_statistics(ndvi_result)

        return {
            "status": "success",
            "name": request.name,
            "statistics": stats,
            "bbox": bbox
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))