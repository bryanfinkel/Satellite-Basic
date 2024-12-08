#app/services/vegetation_analysis.py
import numpy as np
import rasterio
import requests
from io import BytesIO
import logging
from typing import Dict, Optional, List, Tuple
import uuid
from datetime import datetime
import folium
import matplotlib.pyplot as plt
import os
from sqlalchemy.orm import Session
from app.models.vegetation import NDVIAnalysis
from app.schemas.vegetation_schemas import NDVIAnalysisData, AnalysisMetadata

logger = logging.getLogger(__name__)

class VegetationAnalysis:
    def __init__(self, db: Session = None):
        self._analyses = {}
        self.db = db

    @staticmethod
    async def fetch_band_data(url: str) -> Tuple[np.ndarray, Optional[Dict]]:
        """Fetch band data from URL and return as numpy array"""
        try:
            logger.info(f"Fetching band data from {url}")
            response = requests.get(url)
            response.raise_for_status()
            
            with rasterio.open(BytesIO(response.content)) as dataset:
                band_data = dataset.read(1).astype(np.float32)
                metadata = dataset.meta
                
            logger.info(f"Successfully fetched band data, shape: {band_data.shape}")
            return band_data, metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch band data: {str(e)}")
            raise

    async def compute_ndvi(self, red_url: str, nir_url: str) -> np.ndarray:
        """Compute NDVI from red and NIR band URLs"""
        try:
            logger.info("Starting NDVI computation")
            
            red_data, red_meta = await self.fetch_band_data(red_url)
            nir_data, nir_meta = await self.fetch_band_data(nir_url)
            
            if red_data.shape != nir_data.shape:
                raise ValueError(f"Band shapes don't match: Red {red_data.shape} vs NIR {nir_data.shape}")
            
            logger.info(f"Band data shapes: {red_data.shape}")
            
            valid_mask = (red_data > 0) & (nir_data > 0)
            ndvi_array = np.full(red_data.shape, np.nan, dtype=np.float32)
            
            sum_bands = nir_data + red_data
            diff_bands = nir_data - red_data
            
            valid_divisor = sum_bands != 0
            compute_mask = valid_mask & valid_divisor
            
            ndvi_array[compute_mask] = diff_bands[compute_mask] / sum_bands[compute_mask]
            ndvi_array = np.clip(ndvi_array, -1, 1)
            
            logger.info(f"NDVI computation successful. Range: [{np.nanmin(ndvi_array)}, {np.nanmax(ndvi_array)}]")
            return ndvi_array
            
        except Exception as e:
            logger.error(f"NDVI computation failed: {str(e)}")
            raise

    async def store_analysis(self, ndvi_array: np.ndarray, metadata: AnalysisMetadata) -> str:
        try:
            analysis_id = str(uuid.uuid4())
            
            # Convert metadata to dict for storage
            metadata_dict = metadata.model_dump()
        
            # Before downsampling
            logger.info(f"Original array shape: {ndvi_array.shape}")
            logger.info(f"Original memory size: {ndvi_array.nbytes / 1024 / 1024:.2f} MB")

            # Downsample and replace NaN with None for JSON compatibility
            downsampled = ndvi_array[::10, ::10]  # Take every 10th value
            downsampled_list = np.where(np.isnan(downsampled), None, downsampled).tolist()

            logger.info(f"Downsampled shape: {downsampled.shape}")
            logger.info(f"Downsampled size: {downsampled.nbytes / 1024 / 1024:.2f} MB")

            # Variables holding image data:

            # ndvi_array: Full resolution numpy array in memory
            # downsampled: Reduced resolution numpy array for database
            # self._analyses[analysis_id]["ndvi_array"]: Full resolution in memory cache
            # db_analysis.ndvi_array: Downsampled in database

            
            # Store in database
            analysis = NDVIAnalysis(
                id=analysis_id,
                name=metadata.name,
                bbox=metadata.bbox,
                ndvi_stats=await self.compute_statistics(ndvi_array),
                # ndvi_array=ndvi_array.tolist(), 
                # ndvi_array=downsampled.tolist(),  # Store downsampled version
                ndvi_array=downsampled_list,  # Use cleaned array

                red_url=metadata.red_url,
                nir_url=metadata.nir_url
            )

            
            self.db.add(analysis)
            self.db.commit()
            
            # Keep in memory for visualization
            # Keep full resolution in memory
            self._analyses[analysis_id] = {
                "ndvi_array": ndvi_array,
                # "metadata": metadata
                "metadata": metadata.model_dump()
            }
            
            return analysis_id
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to store analysis: {str(e)}")
            raise

    async def create_map_display(self, ndvi_array: np.ndarray, bbox: List[float],
                               title: str = "NDVI Analysis") -> folium.Map:
        """Create an interactive map with NDVI visualization"""
        try:
            ndvi_array = np.squeeze(ndvi_array)
            if ndvi_array.ndim != 2:
                raise ValueError("NDVI array must be 2-dimensional")
            
            ndvi_array = ndvi_array.astype(np.float32)
            ndvi_array = np.nan_to_num(ndvi_array, nan=-9999)
            
            # Calculate center point for map
            center_lat = (bbox[1] + bbox[3]) / 2
            center_lon = (bbox[0] + bbox[2]) / 2
            
            # Create base map
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

    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve analysis results by ID"""
        try:
            # Check memory cache first
            if analysis_id in self._analyses:
                return self._analyses[analysis_id]
                
            # If not in memory, check database
            db_analysis = self.db.query(NDVIAnalysis).filter(NDVIAnalysis.id == analysis_id).first()
            if db_analysis:
                # Reconstruct analysis data
                return {
                    "ndvi_array": np.array(db_analysis.ndvi_array),  # Convert back to numpy array
                    "metadata": {
                        "name": db_analysis.name,
                        "bbox": db_analysis.bbox
                    }
                }
            return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve analysis: {str(e)}")
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