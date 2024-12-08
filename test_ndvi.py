import requests

url = "http://localhost:8000/api/v1/vegetation/ndvi"
payload = {
    "name": "Test Analysis",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [-98.0, 30.0],  # Using central Texas as an example
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

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print(f"Error: {str(e)}")