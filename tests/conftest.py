# File: tests/conftest.py
# Path: Satellite-Basic/tests/conftest.py
# Description: pytest configuration file for async tests and fixtures

import pytest

# Set default fixture loop scope to function level
pytest.asyncio_default_fixture_loop_scope = "function"

# Configure asyncio mode
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )

    # Add to conftest.py
@pytest.fixture
def sample_ndvi_data():
    return np.random.uniform(-1, 1, (100, 100))

@pytest.fixture
def sample_bbox():
    return [-74.0, 40.7, -73.9, 40.8]

# Any test file can use these fixtures - so I think I paste the following code into the file that calls this module
# async def test_new_feature(sample_ndvi_data, sample_bbox):
#     assert sample_ndvi_data.shape == (100, 100)

# and then:
# Run all tests with a single command:
# bash
# pytest tests/ -v