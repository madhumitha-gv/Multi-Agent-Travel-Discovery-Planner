# utils/weather_api.py

import openmeteo_requests
import requests_cache
from retry_requests import retry

URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo accepts many coordinates per request; this keeps each URL a
# sane length while still cutting hundreds of calls down to a handful.
BATCH_SIZE = 100

# Built once. The session caches for an hour and retries on failure, so
# rebuilding it per call just threw that away.
_cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
_client = openmeteo_requests.Client(session=retry(_cache_session, retries=1, backoff_factor=0.2))


def fetch_apparent_temperature(latitude, longitude):
    """Apparent temperature in Celsius for a single location."""
    try:
        responses = _client.weather_api(
            URL,
            params={"latitude": latitude, "longitude": longitude, "current": "apparent_temperature"},
            timeout=8,
        )
        return responses[0].Current().Variables(0).Value()
    except Exception:
        return None


def fetch_apparent_temperatures(coordinates):
    """Apparent temperatures for many locations, batched into few requests.

    `coordinates` is a sequence of (latitude, longitude) pairs; the return
    value is a list of temperatures in the same order. Locations whose
    batch fails come back as None rather than sinking the whole lookup.
    """
    coordinates = list(coordinates)
    temperatures = []

    for start in range(0, len(coordinates), BATCH_SIZE):
        batch = coordinates[start:start + BATCH_SIZE]
        try:
            responses = _client.weather_api(
                URL,
                params={
                    "latitude": [lat for lat, _ in batch],
                    "longitude": [lng for _, lng in batch],
                    "current": "apparent_temperature",
                },
                timeout=8,
            )
            batch_values = [r.Current().Variables(0).Value() for r in responses]
            if len(batch_values) != len(batch):
                raise ValueError("Weather response count mismatch")
            temperatures.extend(batch_values)
        except Exception:
            temperatures.extend([None] * len(batch))

    return temperatures
