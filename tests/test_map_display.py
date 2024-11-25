# File: tests/test_map_display.py
# Path: Satellite-Basic/tests/test_map_display.py
# Description: Test suite for map visualization functionality
# - Tests async map creation
# - Tests NDVI visualization
# - Handles async test execution

import pytest
import numpy as np
import os
from app.services.vegetation_analysis import VegetationAnalysis

@pytest.fixture
def vegetation_analyzer():
    return VegetationAnalysis()

@pytest.fixture
def sample_ndvi_data():
    return np.random.uniform(-1, 1, (100, 100))

@pytest.fixture
def sample_bbox():
    return [-74.0, 40.7, -73.9, 40.8]  # New York City area

@pytest.mark.asyncio  # Add this decorator to handle async tests
async def test_map_creation(vegetation_analyzer, sample_ndvi_data, sample_bbox):
    """Test creation of interactive map with NDVI visualization"""
    try:
        map_display = await vegetation_analyzer.create_map_display(
            sample_ndvi_data, 
            sample_bbox,
            "Test NDVI Analysis"
        )
        
        # Save map to HTML for visual inspection
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "test_ndvi_map.html")
        map_display.save(output_file)
        
        assert os.path.exists(output_file)
        print(f"Map saved successfully to: {output_file}")
        
    except Exception as e:
        pytest.fail(f"Map creation failed: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])