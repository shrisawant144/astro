"""
Shared fixtures for Vedic Kundali tests.

Uses a well-known birth chart (fixed coordinates) to avoid network calls
in CI.  The geocoding cache is seeded so Nominatim is never hit.
"""

import pytest
import json
import os


@pytest.fixture(autouse=True)
def seed_geocache(tmp_path, monkeypatch):
    """Seed the geocoding cache so tests never hit the network."""
    cache_file = tmp_path / ".geocache.json"
    cache_data = {
        "mumbai, india": [19.0760, 72.8777],
        "mumbai, maharashtra, india": [19.0760, 72.8777],
        "new delhi, india": [28.6139, 77.2090],
        "london, uk": [51.5074, -0.1278],
    }
    cache_file.write_text(json.dumps(cache_data))

    # Patch the cache module to use our temp file
    import kundali.cache as cache_mod
    monkeypatch.setattr(cache_mod, "_CACHE_FILE", str(cache_file))
    monkeypatch.setattr(cache_mod, "_geo_cache", cache_data.copy())

    # Also prevent any real network calls via Nominatim
    def _fake_geocode(place, timeout=15):
        return None  # should never be reached due to cache hit

    geo = cache_mod.get_geocoder()
    monkeypatch.setattr(geo, "geocode", _fake_geocode)


# Known test chart: Mumbai, 1990-05-15 08:30
MUMBAI_BIRTH = {
    "date": "1990-05-15",
    "time": "08:30",
    "place": "Mumbai, India",
    "gender": "Male",
}
