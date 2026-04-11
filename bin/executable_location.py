#!/bin/python

import json

import requests

import os
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
post_data = {"considerIp": "true"}
geolocate_response = requests.post(
    url=f"https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}"
).json()["location"]
lat = geolocate_response["lat"]
lng = geolocate_response["lng"]
geocode_response = requests.post(
    url=f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={API_KEY}",
    data=post_data,
).json()
locality: str = None
country_code: str = None
for component in geocode_response["results"][0]["address_components"]:
    if "locality" in component["types"]:
        locality = component["long_name"]
    if "country" in component["types"]:
        country_code = component["short_name"]
location = dict(location=f"{locality},{country_code}")
with open(os.path.expanduser("~") + "/.local/share/location.json", "w") as f:
    json.dump(
        obj=location,
        fp=f,
        ensure_ascii=True,
    )
