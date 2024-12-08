import requests
import webbrowser
from urllib.parse import urljoin

# Base URL for your FastAPI server
BASE_URL = "http://localhost:8000/api/v1"

def test_workflow():
    # Step 1: Submit analysis request
    analysis_url = urljoin(BASE_URL, "vegetation/ndvi")
    payload = {
        "name": "Test Analysis",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-98.0, 30.0],
                [-98.0, 30.1],
                [-97.9, 30.1],
                [-97.9, 30.0],
                [-98.0, 30.0]
            ]]
        },
        "date_range": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
    }

    print("1. Submitting analysis request...")
    print(f"Attempting to connect to: {analysis_url}")  # Add here

    response = requests.post(analysis_url, json=payload)
    
    if response.status_code != 200:
        print(f"Error: {response.json()}")
        return
    
    result = response.json()
    analysis_id = result["analysis_id"]
    print(f"Analysis ID: {analysis_id}")
    print(f"Statistics: {result['statistics']}")

    # Step 2: Get map visualization
    print("\n2. Getting map visualization...")
    map_url = urljoin(BASE_URL, f"visualization/map/{analysis_id}")
    
    print(f"Map URL: {map_url}")
    print("Opening map in browser...")
    webbrowser.open(map_url)

if __name__ == "__main__":
    test_workflow()