# File: tests/test_vegetation_mock.py
# Path: Satellite-Basic/tests/test_vegetation_mock.py
# Description: Mock tests for vegetation analysis functionality
# - Tests NDVI computation with mock data
# - Tests database operations with mock data
# - Tests analysis storage and retrieval

import pytest
from unittest.mock import Mock, patch
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.vegetation_analysis import VegetationAnalysis
from app.schemas.vegetation_schemas import VegetationAnalysisRequest, Geometry, DateRange

@pytest.fixture
def db():
    db = next(get_db())
    yield db
    db.close()

@pytest.fixture
def mock_ndvi_data():
    """Create mock satellite band data"""
    return np.random.uniform(0, 1, (100, 100))

@pytest.mark.asyncio
async def test_vegetation_analysis_mock(mock_ndvi_data, mocker):
    """Test NDVI computation with mock data"""
    # Create mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"mock_content"
    
    # Mock requests.get
    mocker.patch('requests.get', return_value=mock_response)
    
    # Mock rasterio.open
    mock_dataset = Mock()
    mock_dataset.read.return_value = mock_ndvi_data
    mocker.patch('rasterio.open', return_value=mock_dataset)
    
    va = VegetationAnalysis()
    result = await va.compute_ndvi(
        "https://mock-server.com/red_band",
        "https://mock-server.com/nir_band"
    )
    
    assert isinstance(result, np.ndarray)
    assert result.shape == mock_ndvi_data.shape

@pytest.mark.asyncio
async def test_ndvi_analysis_with_db_mock(db: Session, mock_ndvi_data, mocker):
    """Test database operations with mock data"""
    # Set up mocks
    mocker.patch('requests.get', return_value=Mock(status_code=200, content=b"mock_content"))
    mocker.patch('rasterio.open', return_value=Mock(read=Mock(return_value=mock_ndvi_data)))
    
    va = VegetationAnalysis(db)
    test_request = VegetationAnalysisRequest(
        name="Test DB Analysis",
        geometry=Geometry(
            type="Polygon",
            coordinates=[[[-122.5, 37.7], [-122.4, 37.7], 
                         [-122.4, 37.8], [-122.5, 37.8], 
                         [-122.5, 37.7]]]
        ),
        date_range=DateRange(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
    )
    
    # Test analysis workflow
    ndvi_result = await va.compute_ndvi(
        "https://mock-server.com/red_band",
        "https://mock-server.com/nir_band"
    )
    
    analysis_id = await va.store_analysis(ndvi_result, {
        "name": test_request.name,
        "bbox": [-122.5, 37.7, -122.4, 37.8],
        "red_url": "https://mock-server.com/red_band",
        "nir_url": "https://mock-server.com/nir_band"
    })
    
    assert analysis_id is not None
    stored_analysis = await va.get_analysis(analysis_id)
    assert stored_analysis is not None
    assert stored_analysis["metadata"]["name"] == test_request.name