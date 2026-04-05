"""
Caching layer for expensive operations: geocoding and timezone lookups.

Singletons avoid re-instantiating heavy objects (TimezoneFinder, Nominatim)
on every call.  Geocoding results are cached in-memory and persisted to a
small JSON file so repeated lookups for the same city are near-instant.
"""

import json
import os
import threading

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Singleton TimezoneFinder (takes ~0.5 s to construct)
# ---------------------------------------------------------------------------
_tf_instance = None


def get_timezone_finder():
    """Return a shared TimezoneFinder instance (thread-safe lazy init)."""
    global _tf_instance
    if _tf_instance is None:
        with _lock:
            if _tf_instance is None:
                _tf_instance = TimezoneFinder()
    return _tf_instance


# ---------------------------------------------------------------------------
# Singleton Nominatim geocoder
# ---------------------------------------------------------------------------
_geocoder = None


def get_geocoder():
    """Return a shared Nominatim geocoder instance."""
    global _geocoder
    if _geocoder is None:
        with _lock:
            if _geocoder is None:
                _geocoder = Nominatim(user_agent="vedic_kundali_cli")
    return _geocoder


# ---------------------------------------------------------------------------
# Geocoding cache  (in-memory dict + optional JSON file on disk)
# ---------------------------------------------------------------------------
_geo_cache: dict = {}
_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".geocache.json")


def _load_cache():
    global _geo_cache
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r") as f:
                _geo_cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            _geo_cache = {}


def _save_cache():
    try:
        with open(_CACHE_FILE, "w") as f:
            json.dump(_geo_cache, f, indent=1)
    except IOError:
        pass


# Load on first import
_load_cache()


def get_lat_lon_cached(place):
    """Geocode a place string with in-memory + disk cache.

    Returns:
        tuple[float, float]: (latitude, longitude)

    Raises:
        ValueError: If the place cannot be geocoded.
    """
    key = place.strip().lower()
    if key in _geo_cache:
        return tuple(_geo_cache[key])

    geo = get_geocoder()
    loc = geo.geocode(place, timeout=15)
    if not loc:
        raise ValueError(
            f"Location not found: {place}. Try 'Mumbai, Maharashtra, India'"
        )

    result = (loc.latitude, loc.longitude)
    _geo_cache[key] = list(result)
    _save_cache()
    return result
