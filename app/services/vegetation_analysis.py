
# File: app/services/vegetation_analysis.py
# Path: Satellite-Basic/app/services/vegetation_analysis.py
# Description: Vegetation health analysis using NDVI and MSAVI
#   - Calculates NDVI and MSAVI indices
#   - Assesses vegetation health and coverage

import numpy as np
import rasterio
import requests
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class VegetationAnalysis:
    @staticmethod
    async def fetch_band_data(url: str):
        """Fetch band data from URL and return as rasterio dataset"""
        response = requests.get(url)
        if response.status_code == 200:
            return rasterio.open(BytesIO(response.content))
        else:
            raise Exception(f"Failed to fetch band data: {response.status_code}")

    async def compute_ndvi(self, red_url: str, nir_url: str):
        """
        Compute NDVI from red and NIR band URLs
        Adapted from friend's utils.py
        """
        try:
            red_band = await self.fetch_band_data(red_url)
            nir_band = await self.fetch_band_data(nir_url)

            red = red_band.read(1).astype(float)
            nir = nir_band.read(1).astype(float)

            # Compute NDVI
            ndvi = np.divide((nir - red), (nir + red), 
                           out=np.zeros_like(nir), 
                           where=(nir + red) != 0)

            # Handle invalid values
            ndvi = np.where(np.isfinite(ndvi), ndvi, np.nan)
            return ndvi

        except Exception as e:
            logger.error(f"NDVI computation failed: {str(e)}")
            raise

    @staticmethod
    async def compute_statistics(ndvi):
        """
        Compute statistics for NDVI values
        Adapted from friend's utils.py
        """
        try:
            ndvi_flat = ndvi.flatten()
            ndvi_flat = ndvi_flat[~np.isnan(ndvi_flat)]
            return {
                "min": float(np.min(ndvi_flat)),
                "max": float(np.max(ndvi_flat)),
                "mean": float(np.mean(ndvi_flat))
            }
        except Exception as e:
            logger.error(f"Statistics computation failed: {str(e)}")
            raise