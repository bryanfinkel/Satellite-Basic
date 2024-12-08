import asyncio
from app.services.vegetation_analysis import VegetationAnalysis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_ndvi():
    # URLs we got from test_stac.py
    red_url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/14/R/NU/2024/1/S2A_14RNU_20240131_0_L2A/B04.tif"
    nir_url = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/14/R/NU/2024/1/S2A_14RNU_20240131_0_L2A/B08.tif"
    
    try:
        # Create VegetationAnalysis instance
        va = VegetationAnalysis()
        
        # Step 1: Compute NDVI
        print("Computing NDVI...")
        ndvi_result = await va.compute_ndvi(red_url, nir_url)
        print("NDVI computed successfully!")
        
        # Step 2: Store the analysis
        print("Storing analysis...")
        analysis_id = await va.store_analysis(ndvi_result, {
            "name": "Test Analysis",
            "red_url": red_url,
            "nir_url": nir_url
        })
        print(f"Analysis stored with ID: {analysis_id}")
        
        return analysis_id
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    analysis_id = asyncio.run(test_simple_ndvi())