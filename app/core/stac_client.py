# File: app/core/stac_client.py
# Path: Satellite-Basic/app/core/stac_client.py
# Description: STAC Client interface for AWS Earth Search API
# - Handles satellite imagery search and retrieval
# - Manages STAC API connections and queries
# - Processes search criteria (bbox, dates, bands)

from pystac_client import Client
from typing import Dict, List, Tuple
import logging
import json

logger = logging.getLogger(__name__)

class STACClient:
    def __init__(self):
        """Initialize STAC client with AWS Earth Search endpoint"""
        try:
            self.search_url = "https://earth-search.aws.element84.com/v1"
            self.client = Client.open(self.search_url)
        except Exception as e:
            logger.error(f"Failed to initialize STAC client: {str(e)}")
            raise

    async def search_images(
        self,
        bbox: List[float],
        date_range: Tuple[str, str],
        collections: List[str] = ["sentinel-2-l2a"],
        max_items: int = 3
    ) -> Dict:
        """Search for satellite imagery"""
        try:
            search = self.client.search(
                collections=collections,
                bbox=bbox,
                datetime=f"{date_range[0]}/{date_range[1]}",
                limit=400,
                max_items=max_items
            )

            # Convert STAC items to dictionaries to avoid recursion
            items = [item.to_dict() for item in search.item_collection()]
            logger.info(f"Found {len(items)} items")
            
            return {
                "status": "success",
                "count": len(items),
                "items": items
            }
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }