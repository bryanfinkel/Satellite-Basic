# File: tests/test_vegetation_real.py
# Path: Satellite-Basic/tests/test_vegetation_real.py
# Description: Integration tests with real Sentinel-2 data
# - Tests STAC API integration
# - Tests real data NDVI computation
# - Tests end-to-end analysis workflow

import pytest
from app.core.stac_client import STACClient
from app.services.vegetation_analysis import VegetationAnalysis
from app.schemas.vegetation_schemas import VegetationAnalysisRequest, Geometry, DateRange

@pytest.mark.asyncio
async def test_vegetation_analysis_real():
    """Test NDVI computation with real Sentinel-2 data"""
    # Initialize STAC client
    stac_client = STACClient()
    
    # Search for imagery
    search_results = await stac_client.search_images(
        bbox=[-122.5, 37.7, -122.4, 37.8],  # San Francisco area
        date_range=("2024-01-01", "2024-01-31")
    )
    
    assert search_results["status"] == "success"
    assert len(search_results["items"]) > 0
    
    # Get band URLs from first item
    item = search_results["items"][0]
    red_url = item["assets"]["red"]["href"]
    nir_url = item["assets"]["nir"]["href"]
    
    # Perform analysis
    va = VegetationAnalysis()
    result = await va.compute_ndvi(red_url, nir_url)
    
    assert result is not None