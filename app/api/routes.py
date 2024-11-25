# File: app/api/routes.py
# Path: Satellite-Basic/app/api/routes.py
# Description: API routes for satellite analysis and visualization

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vegetation_analysis import VegetationAnalysis
from app.services.visualization_service import VisualizationService
from app.core.stac_client import STACClient
from app.schemas.vegetation_schemas import VegetationAnalysisRequest
from fastapi.responses import HTMLResponse
from typing import Optional, Dict, List
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Initialize services
router = APIRouter()
stac_client = STACClient()
vegetation_service = VegetationAnalysis()
visualization_service = VisualizationService()

@router.get("/ndvi-map/{analysis_id}", response_class=HTMLResponse)
async def get_ndvi_map(analysis_id: str, db: Session = Depends(get_db)):
    try:
        # Initialize vegetation service with database session
        va = VegetationAnalysis(db)
        
        # Get the analysis data
        analysis = await va.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        # Create map using the stored NDVI array
        map_display = await va.create_map_display(
            ndvi_array=analysis["ndvi_array"],
            bbox=analysis["metadata"]["bbox"],
            title=f"NDVI Analysis: {analysis['metadata']['name']}"
        )
        
        return map_display._repr_html_()
        
    except Exception as e:
        logger.error(f"Failed to generate NDVI map: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/analyze-area")
async def analyze_area(
    bbox: list[float],
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Analyze an area and create NDVI visualization"""
    try:
        # Initialize vegetation service with database session
        va = VegetationAnalysis(db)
        
        # Get satellite imagery
        search_results = await stac_client.search_images(
            bbox=bbox,
            date_range=(start_date, end_date)
        )
        
        if not search_results["items"]:
            raise HTTPException(status_code=404, detail="No imagery found")
            
        # Get first item
        item = search_results["items"][0]
        red_url = item["assets"]["red"]["href"]
        nir_url = item["assets"]["nir"]["href"]
        
        # Compute NDVI
        ndvi_result = await va.compute_ndvi(red_url, nir_url)
        
        # Store analysis
        analysis_id = await va.store_analysis(ndvi_result, {
            "name": f"Area Analysis {start_date}",
            "bbox": bbox,
            "red_url": red_url,
            "nir_url": nir_url
        })
        
        return {"analysis_id": analysis_id}
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
async def analyze_vegetation(
    request: VegetationAnalysisRequest,
    db: Session = Depends(get_db)
):
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

        # Initialize vegetation service with db session
        va = VegetationAnalysis(db)

        # Search for images
        items = await stac_client.search_images(
            bbox=bbox,
            date_range=(request.date_range.start_date, request.date_range.end_date)
        )

        if not items['items']:
            raise HTTPException(status_code=404, detail="No imagery found")

        # Process NDVI
        ndvi_result = await va.compute_ndvi(
            items['items'][0]['assets']['red']['href'],
            items['items'][0]['assets']['nir']['href']
        )

        # Store analysis and get ID
        analysis_id = await va.store_analysis(ndvi_result, {
            "name": request.name,
            "bbox": bbox,
            "red_url": items['items'][0]['assets']['red']['href'],
            "nir_url": items['items'][0]['assets']['nir']['href']
        })

        # Compute statistics
        stats = await va.compute_statistics(ndvi_result)

        return {
            "status": "success",
            "analysis_id": analysis_id,
            "name": request.name,
            "statistics": stats,
            "bbox": bbox
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization/map/{analysis_id}", response_class=HTMLResponse)
async def get_map(analysis_id: str, db: Session = Depends(get_db)):
    try:
        # Initialize vegetation service
        va = VegetationAnalysis(db)
        
        # Get analysis data
        analysis = await va.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Create map
        map_display = await va.create_map_display(
            ndvi_array=analysis["ndvi_array"],
            bbox=analysis["metadata"]["bbox"],
            title=f"NDVI Analysis: {analysis['metadata']['name']}"
        )

        # Return HTML representation
        return map_display._repr_html_()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

