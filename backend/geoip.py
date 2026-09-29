import random

MOCK_GEO_DATA = {
    "192.168.1.1": {"country": "Internal", "city": "Local Network", "lat": 0.0, "lon": 0.0, "timezone": "UTC"},
    "8.8.8.8": {"country": "US", "city": "Mountain View", "lat": 37.386, "lon": -122.0838, "timezone": "America/Los_Angeles"},
    "1.1.1.1": {"country": "AU", "city": "Research", "lat": -37.7667, "lon": 145.1833, "timezone": "Australia/Melbourne"},
    "93.184.216.34": {"country": "US", "city": "Norwell", "lat": 42.1508, "lon": -70.8228, "timezone": "America/New_York"}
}

def lookup_ip(ip_address: str) -> dict:
    if not ip_address:
        return {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0, "timezone": "UTC"}
        
    if ip_address in MOCK_GEO_DATA:
        return MOCK_GEO_DATA[ip_address]
        
    if ip_address.startswith("10.") or ip_address.startswith("192.168."):
         return {"country": "Internal", "city": "Local Network", "lat": 0.0, "lon": 0.0, "timezone": "UTC"}

    lat = random.uniform(-90.0, 90.0)
    lon = random.uniform(-180.0, 180.0)
    
    return {
        "country": "Unknown External",
        "city": "Unknown City",
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "timezone": "UTC"
    }
