#!/usr/bin/env python3

import os
import sys
import json
import requests
from pathlib import Path

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    print("Error: GOOGLE_MAPS_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)
LOCATION_FILE = Path.home() / ".local" / "share" / "location.json"

def main():
    post_data = {"considerIp": "true"}
    
    try:
        # 1. Geolocate based on IP
        geo_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}"
        geolocate_resp = requests.post(geo_url, timeout=10)
        geolocate_resp.raise_for_status()
        location_data = geolocate_resp.json().get("location")
        
        if not location_data:
            print("Error: Could not determine location from IP.", file=sys.stderr)
            sys.exit(1)
            
        lat, lng = location_data["lat"], location_data["lng"]

        # 2. Reverse Geocode to get locality and country
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={API_KEY}"
        geocode_resp = requests.post(geocode_url, timeout=10)
        geocode_resp.raise_for_status()
        geocode_data = geocode_resp.json()
        
        if not geocode_data.get("results"):
            print("Error: No geocoding results found.", file=sys.stderr)
            sys.exit(1)

        locality = "Unknown"
        country_code = "XX"
        
        for component in geocode_data["results"][0]["address_components"]:
            if "locality" in component["types"]:
                locality = component["long_name"]
            if "country" in component["types"]:
                country_code = component["short_name"]

        # 3. Save to file
        LOCATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        result = {"location": f"{locality},{country_code}"}
        
        with open(LOCATION_FILE, "w") as f:
            json.dump(result, f, ensure_ascii=True)
            
        print(f"Location updated: {locality}, {country_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error updating location: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
