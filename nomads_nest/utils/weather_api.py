# utils/weather_api.py

import openmeteo_requests
import requests_cache
from retry_requests import retry

def fetch_apparent_temperature(latitude, longitude):
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "apparent_temperature"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    current = response.Current()
    return current.Variables(0).Value()  # Returns apparent temp in Celsius
