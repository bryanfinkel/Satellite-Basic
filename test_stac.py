import asyncio
from app.core.stac_client import STACClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_stac_search():
    stac_client = STACClient()
    
    bbox = [-98.0, 30.0, -97.9, 30.1]  # Central Texas
    date_range = ("2024-01-01", "2024-01-31")
    
    try:
        results = await stac_client.search_images(bbox, date_range)
        
        if results and 'items' in results:
            print(f"Found {len(results['items'])} images")
            
            if results['items']:
                item = results['items'][0]
                print("\nFirst item assets:")
                print(f"Red band URL: {item['assets'].get('red', {}).get('href', 'Not found')}")
                print(f"NIR band URL: {item['assets'].get('nir', {}).get('href', 'Not found')}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error during search: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_stac_search())