# File: app/services/visualization_service.py
# Path: Satellite-Basic/app/services/visualization_service.py
# Description: Visualization Service for satellite imagery analysis
# - Creates interactive maps using folium
# - Handles NDVI visualization and overlays
# - Manages map controls and styling

import folium # previously tried ipleaflet, go back and check that out later
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class VisualizationService:
    def __init__(self):
        """Initialize visualization service"""
        self.output_dir = 'temp'
        os.makedirs(self.output_dir, exist_ok=True)

    def create_base_map(self, bbox: List[float]) -> folium.Map:
        """Create interactive base map centered on analysis area"""
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2
        
        return folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles='OpenStreetMap'
        )

    def visualize_ndvi(self, 
                      ndvi_array: np.ndarray, 
                      bbox: List[float], 
                      title: str = "NDVI Analysis",
                      output_path: Optional[str] = None) -> folium.Map:
        """Create NDVI visualization with interactive map"""
        try:
            # Create base map
            m = self.create_base_map(bbox)

            # Generate unique filename for the overlay
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = os.path.join(self.output_dir, f'ndvi_overlay_{timestamp}.png')

            # Create NDVI visualization
            plt.figure(figsize=(10, 10))
            img = plt.imshow(ndvi_array, cmap='RdYlGn', vmin=-1, vmax=1)
            plt.colorbar(img, label='NDVI')
            plt.title(title)
            plt.axis('off')
            plt.savefig(temp_file)
            plt.close()

            # Add NDVI overlay to map
            img_bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
            folium.raster_layers.ImageOverlay(
                temp_file,
                bounds=img_bounds,
                opacity=0.7,
                name='NDVI'
            ).add_to(m)

            # Add layer control
            folium.LayerControl().add_to(m)

            # Save map if output path provided
            if output_path:
                m.save(output_path)

            return m

        except Exception as e:
            logger.error(f"Failed to create NDVI visualization: {str(e)}")
            raise

    def add_polygon_overlay(self, 
                          m: folium.Map, 
                          coordinates: List[List[float]], 
                          popup: str = None) -> folium.Map:
        """Add polygon overlay to highlight areas of interest"""
        try:
            folium.Polygon(
                locations=coordinates,
                popup=popup,
                color='red',
                fill=True,
                weight=2
            ).add_to(m)
            return m
        except Exception as e:
            logger.error(f"Failed to add polygon overlay: {str(e)}")
            raise