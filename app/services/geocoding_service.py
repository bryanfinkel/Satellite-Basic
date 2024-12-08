from geopy.geocoders import Nominatim
from geopy.distance import geodesic

class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="satellite-basic")
    
    async def get_location_bbox(self, location: str, distance_km: float):
        location = self.geolocator.geocode(location)
        if not location:
            raise ValueError(f"Location not found: {location}")
            
        center = (location.latitude, location.longitude)
        
        # Calculate bbox corners
        north = geodesic(kilometers=distance_km/2).destination(center, 0)
        south = geodesic(kilometers=distance_km/2).destination(center, 180)
        east = geodesic(kilometers=distance_km/2).destination(center, 90)
        west = geodesic(kilometers=distance_km/2).destination(center, 270)
        
        return [
            west.longitude, south.latitude,
            east.longitude, north.latitude
        ]
