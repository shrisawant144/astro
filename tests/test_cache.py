"""Tests for kundali.cache — singleton and caching behaviour."""

import pytest


class TestSingletons:
    """Verify that singletons return the same instance."""

    def test_timezone_finder_singleton(self):
        from kundali.cache import get_timezone_finder
        tf1 = get_timezone_finder()
        tf2 = get_timezone_finder()
        assert tf1 is tf2

    def test_geocoder_singleton(self):
        from kundali.cache import get_geocoder
        g1 = get_geocoder()
        g2 = get_geocoder()
        assert g1 is g2


class TestGeocache:
    """Verify geocoding cache hits and misses."""

    def test_cached_lookup_hits(self):
        from kundali.cache import get_lat_lon_cached
        lat, lon = get_lat_lon_cached("Mumbai, India")
        assert abs(lat - 19.076) < 0.01
        assert abs(lon - 72.877) < 0.01

    def test_unknown_place_raises(self):
        from kundali.cache import get_lat_lon_cached
        with pytest.raises(ValueError, match="Location not found"):
            get_lat_lon_cached("Xyzzy Nonexistent Place 12345")
