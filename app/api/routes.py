from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vegetation_analysis import VegetationAnalysis
from app.services.visualization_service import VisualizationService
from app.services.geocoding_service import GeocodingService
from app.core.stac_client import STACClient
from app.schemas.vegetation_schemas import (
    VegetationAnalysisRequest, 
    AnalysisMetadata,
    LocationAnalysisRequest,
    DateRange
)
from fastapi.responses import HTMLResponse
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
stac_client = STACClient()
visualization_service = VisualizationService()

@router.post("/vegetation/ndvi")
async def analyze_vegetation(
    request: VegetationAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze vegetation using NDVI"""
    try:
        logger.info(f"Processing vegetation analysis request for area: {request.name}")
        
        coords = request.geometry.coordinates[0]
        bbox = [
            min(x[0] for x in coords),  # min_lon
            min(x[1] for x in coords),  # min_lat
            max(x[0] for x in coords),  # max_lon
            max(x[1] for x in coords)   # max_lat
        ]
        
        va = VegetationAnalysis(db)
        
        # Search for images
        items = await stac_client.search_images(
            bbox=bbox,
            date_range=(request.date_range.start_date, request.date_range.end_date)
        )

        if not items.get('items'):
            raise HTTPException(status_code=404, detail="No imagery found")

        # Process NDVI
        ndvi_result = await va.compute_ndvi(
            items['items'][0]['assets']['red']['href'],
            items['items'][0]['assets']['nir']['href']
        )

        # Create metadata with validated data
        metadata = AnalysisMetadata(
            name=request.name,
            bbox=bbox,
            red_url=items['items'][0]['assets']['red']['href'],
            nir_url=items['items'][0]['assets']['nir']['href']
        )
        
        # Store analysis
        analysis_id = await va.store_analysis(ndvi_result, metadata)

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
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/visualization/map/{analysis_id}", response_class=HTMLResponse)
async def get_map(analysis_id: str, db: Session = Depends(get_db)):
    """Get map visualization for a specific analysis"""
    try:
        va = VegetationAnalysis(db)
        
        analysis = await va.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        map_display = await va.create_map_display(
            ndvi_array=analysis["ndvi_array"],
            bbox=analysis["metadata"]["bbox"],
            title=f"NDVI Analysis: {analysis['metadata']['name']}"
        )

        return map_display._repr_html_()

    except Exception as e:
        logger.error(f"Failed to generate map: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/vegetation/location")
async def analyze_location(
    request: LocationAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze vegetation for location"""
    try:
        # Get bbox from location
        geocoding = GeocodingService()
        bbox = await geocoding.get_location_bbox(request.location, request.distance_km)
        
        # Create geometry
        geometry = {
            "type": "Polygon",
            "coordinates": [[
                [bbox[0], bbox[1]],  # SW
                [bbox[0], bbox[3]],  # NW
                [bbox[2], bbox[3]],  # NE
                [bbox[2], bbox[1]],  # SE
                [bbox[0], bbox[1]]   # SW (close polygon)
            ]]
        }
        
        # Convert to vegetation request
        veg_request = VegetationAnalysisRequest(
            name=f"Analysis: {request.location}",
            geometry=geometry,
            date_range=DateRange(
                start_date="2024-01-01",
                end_date="2024-01-31"
            )
        )
        
        return await analyze_vegetation(veg_request, db)
    except Exception as e:
        logger.error(f"Location analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    