# File: app/services/vegetation_analysis.py
# Path: Satellite-Basic/app/services/vegetation_analysis.py
# Description: Vegetation health analysis with map visualization capabilities
# - Calculates NDVI indices
# - Creates interactive map visualizations
# - Stores analysis results
# - Handles data visualization and feature highlighting

import numpy as np
import asyncio
import rasterio
import requests
from io import BytesIO
import logging
from typing import Dict, Optional, List
import uuid
from sqlalchemy.orm import Session
from app.models.vegetation import NDVIAnalysis
from shapely.geometry import Polygon
import folium
import matplotlib.pyplot as plt
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class VegetationAnalysis:
    def __init__(self, db: Session = None):
        """Initialize with optional database session"""
        self._analyses = {}
        self.db = db
        
    @staticmethod
    async def fetch_band_data(url: str):
        """Fetch band data from URL and return as rasterio dataset"""
        response = requests.get(url)
        if response.status_code == 200:
            return rasterio.open(BytesIO(response.content))
        else:
            raise Exception(f"Failed to fetch band data: {response.status_code}")

    async def compute_ndvi(self, red_url: str, nir_url: str):
        """Compute NDVI from red and NIR band URLs"""
        try:
            red_band = await self.fetch_band_data(red_url)
            nir_band = await self.fetch_band_data(nir_url)
            
            red = red_band.read(1).astype(float)
            nir = nir_band.read(1).astype(float)
            
            ndvi = np.divide((nir - red), (nir + red),
                           out=np.zeros_like(nir),
                           where=(nir + red) != 0)
            
            ndvi = np.where(np.isfinite(ndvi), ndvi, np.nan)
            return ndvi
            
        except Exception as e:
            logger.error(f"NDVI computation failed: {str(e)}")
            raise

    async def create_map_display(self, ndvi_array: np.ndarray, bbox: List[float],
                            title: str = "NDVI Analysis") -> folium.Map:
        try:
            # Ensure array is 2D and proper type
            ndvi_array = np.squeeze(ndvi_array)
            if ndvi_array.ndim != 2:
                raise ValueError("NDVI array must be 2-dimensional")
                
            ndvi_array = ndvi_array.astype(np.float32)
            ndvi_array = np.nan_to_num(ndvi_array, nan=-9999)
            
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
            
            m = folium.Map(location=[center_lat, center_lon],
                        zoom_start=12,
                        tiles='OpenStreetMap')
            
            # Create temporary directory if it doesn't exist
            os.makedirs('temp', exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = f'temp/ndvi_{timestamp}.png'
            
            # Create and save NDVI visualization
            plt.figure(figsize=(10, 10))
            plt.imshow(ndvi_array, cmap='RdYlGn', vmin=-1, vmax=1)
            plt.colorbar(label='NDVI')
            plt.title(title)
            plt.axis('off')
            plt.savefig(temp_file)
            plt.close()
            
            # Add image overlay to map
            img_bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            folium.raster_layers.ImageOverlay(
                temp_file,
                bounds=img_bounds,
                opacity=0.7,
                name='NDVI'
            ).add_to(m)
            
            folium.LayerControl().add_to(m)
            
            return m
            
        except Exception as e:
            logger.error(f"Map creation failed: {str(e)}")
            raise
        
    @staticmethod
    async def compute_statistics(ndvi):
        """Compute statistics for NDVI values"""
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

    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve analysis results by ID"""
        try:
            # First check in-memory storage
            if analysis_id in self._analyses:
                return self._analyses[analysis_id]
                
            # Then check database
            if self.db:
                db_analysis = self.db.query(NDVIAnalysis).filter(
                    NDVIAnalysis.id == analysis_id
                ).first()
                
                if db_analysis:
                    # Ensure proper array reconstruction
                    ndvi_array = np.array(db_analysis.ndvi_stats.get("ndvi_array", []), 
                                        dtype=np.float32)
                    ndvi_array = np.squeeze(ndvi_array)
                    if ndvi_array.ndim != 2:
                        raise ValueError("NDVI array must be 2-dimensional")
                        
                    return {
                        "ndvi_array": ndvi_array,
                        "metadata": {
                            "name": db_analysis.name,
                            "bbox": db_analysis.bbox,
                            "stats": db_analysis.ndvi_stats
                        }
                    }
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {str(e)}")
            raise

    async def _execute_with_retry(self, operation):
        """Helper method to retry database operations"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Database operation failed, attempt {attempt + 1}/{max_retries}")
                if self.db:
                    self.db.rollback()
                await asyncio.sleep(retry_delay)


    async def store_analysis(self, ndvi_array: np.ndarray, metadata: Dict) -> str:
        """Store analysis results and return analysis_id"""
        async def _store():
            try:
                analysis_id = str(uuid.uuid4())
                
                # Ensure ndvi_array is 2D and proper type
                ndvi_array = np.squeeze(ndvi_array)
                if ndvi_array.ndim != 2:
                    raise ValueError("NDVI array must be 2-dimensional")
                    
                ndvi_array = ndvi_array.astype(np.float32)
                ndvi_array = np.nan_to_num(ndvi_array, nan=-9999)
                
                # Store in memory with proper structure
                self._analyses[analysis_id] = {
                    "ndvi_array": ndvi_array,
                    "metadata": metadata
                }

                if self.db and metadata.get('bbox') and metadata.get('name'):
                    # Store only statistics in database
                    ndvi_stats = await self.compute_statistics(ndvi_array)
                    
                    polygon = Polygon([
                        (metadata['bbox'][0], metadata['bbox'][1]),
                        (metadata['bbox'][2], metadata['bbox'][1]),
                        (metadata['bbox'][2], metadata['bbox'][3]),
                        (metadata['bbox'][0], metadata['bbox'][3]),
                        (metadata['bbox'][0], metadata['bbox'][1])
                    ])
                    
                    db_analysis = NDVIAnalysis(
                        id=analysis_id,
                        name=metadata['name'],
                        bbox=metadata['bbox'],
                        geometry=f'SRID=4326;{polygon.wkt}',
                        ndvi_stats=ndvi_stats,
                        red_url=metadata.get('red_url'),
                        nir_url=metadata.get('nir_url')
                    )
                    
                    self.db.add(db_analysis)
                    self.db.commit()
                    
                return analysis_id
                
            except Exception as e:
                logger.error(f"Failed to store analysis: {str(e)}")
                raise
                
        return await self._execute_with_retry(_store)