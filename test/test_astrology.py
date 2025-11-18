"""Tests for astrology service and kundli computation."""

from datetime import date, time

from src.chat.services.astrology_service import astrology_service


def test_compute_kundli_basic() -> None:
    """Test basic kundli computation with valid data."""
    birth_details = {
        "full_name": "Test User",
        "date_of_birth": date(2004, 12, 27),
        "time_of_birth": time(16, 19, 0),
        "place_of_birth": {"latitude": 19.076, "longitude": 72.8777},
        "timezone": "Asia/Kolkata",
    }

    kundli = astrology_service.compute_kundli(birth_details)

    # Verify structure
    assert isinstance(kundli, dict)
    assert "birth_details" in kundli
    assert "planetary_positions" in kundli
    assert "houses" in kundli
    assert "ascendant" in kundli
    assert "dashas" in kundli
    assert "astrological_context" in kundli
    assert "metadata" in kundli

    # Verify astrological context
    context = kundli["astrological_context"]
    assert "house_meanings" in context
    assert "planet_significations" in context
    assert "7th_house" in context["house_meanings"]
    assert "Venus" in context["planet_significations"]

    # Verify birth details
    birth_data = kundli["birth_details"]
    assert birth_data["date"] == "2004-12-27"
    assert birth_data["time"] == "16:19:00"
    assert birth_data["latitude"] == 19.076
    assert birth_data["longitude"] == 72.8777

    # Verify metadata
    metadata = kundli["metadata"]
    assert metadata["ayanamsha"] == "Lahiri"
    assert metadata["source"] == "jyotishyamitra"
    assert "generated_at" in metadata


def test_compute_kundli_has_planetary_positions() -> None:
    """Test that kundli contains all major planetary positions."""
    birth_details = {
        "date_of_birth": date(1990, 5, 15),
        "time_of_birth": time(14, 30, 0),
        "place_of_birth": {"latitude": 28.6139, "longitude": 77.2090},  # Delhi
        "timezone": "Asia/Kolkata",
    }

    kundli = astrology_service.compute_kundli(birth_details)

    planets = kundli["planetary_positions"]
    assert isinstance(planets, dict)

    # Check that major planets are present
    expected_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    for planet in expected_planets:
        assert planet in planets, f"Planet {planet} not found in kundli"

        planet_data = planets[planet]
        assert isinstance(planet_data, dict)
        assert "name" in planet_data
        assert "sign" in planet_data
        assert "rashi" in planet_data
        assert "nakshatra" in planet_data


def test_compute_kundli_has_ascendant() -> None:
    """Test that kundli contains ascendant information."""
    birth_details = {
        "date_of_birth": date(1995, 8, 20),
        "time_of_birth": time(10, 15, 0),
        "place_of_birth": {"latitude": 12.9716, "longitude": 77.5946},  # Bangalore
        "timezone": "Asia/Kolkata",
    }

    kundli = astrology_service.compute_kundli(birth_details)

    ascendant = kundli["ascendant"]
    assert isinstance(ascendant, dict)
    assert len(ascendant) > 0

    # Check common ascendant attributes
    if "sign" in ascendant:
        assert isinstance(ascendant["sign"], str)
    if "nakshatra" in ascendant:
        assert isinstance(ascendant["nakshatra"], str)


def test_compute_kundli_with_different_timezones() -> None:
    """Test kundli computation with different timezones."""
    # Test with IST
    birth_details_ist = {
        "date_of_birth": date(2000, 1, 1),
        "time_of_birth": time(12, 0, 0),
        "place_of_birth": {"latitude": 19.076, "longitude": 72.8777},
        "timezone": "Asia/Kolkata",
    }

    kundli_ist = astrology_service.compute_kundli(birth_details_ist)
    assert isinstance(kundli_ist, dict)
    assert "planetary_positions" in kundli_ist

    # Test with UTC
    birth_details_utc = {
        "date_of_birth": date(2000, 1, 1),
        "time_of_birth": time(12, 0, 0),
        "place_of_birth": {"latitude": 51.5074, "longitude": -0.1278},  # London
        "timezone": "UTC",
    }

    kundli_utc = astrology_service.compute_kundli(birth_details_utc)
    assert isinstance(kundli_utc, dict)
    assert "planetary_positions" in kundli_utc


def test_compute_kundli_with_edge_case_times() -> None:
    """Test kundli computation with edge case birth times."""
    # Midnight birth
    birth_details_midnight = {
        "date_of_birth": date(1998, 3, 15),
        "time_of_birth": time(0, 0, 0),
        "place_of_birth": {"latitude": 19.076, "longitude": 72.8777},
        "timezone": "Asia/Kolkata",
    }

    kundli_midnight = astrology_service.compute_kundli(birth_details_midnight)
    assert isinstance(kundli_midnight, dict)
    assert "planetary_positions" in kundli_midnight

    # Just before midnight
    birth_details_late = {
        "date_of_birth": date(1998, 3, 15),
        "time_of_birth": time(23, 59, 59),
        "place_of_birth": {"latitude": 19.076, "longitude": 72.8777},
        "timezone": "Asia/Kolkata",
    }

    kundli_late = astrology_service.compute_kundli(birth_details_late)
    assert isinstance(kundli_late, dict)
    assert "planetary_positions" in kundli_late


def test_compute_kundli_with_negative_coordinates() -> None:
    """Test kundli computation with negative latitude/longitude (Southern/Western hemisphere)."""
    # Sydney, Australia
    birth_details = {
        "date_of_birth": date(1992, 6, 10),
        "time_of_birth": time(15, 30, 0),
        "place_of_birth": {"latitude": -33.8688, "longitude": 151.2093},
        "timezone": "Australia/Sydney",
    }

    kundli = astrology_service.compute_kundli(birth_details)
    assert isinstance(kundli, dict)
    assert "planetary_positions" in kundli
    assert kundli["birth_details"]["latitude"] == -33.8688
    assert kundli["birth_details"]["longitude"] == 151.2093


def test_compute_kundli_data_consistency() -> None:
    """Test that repeated computations with same data produce consistent results."""
    birth_details = {
        "date_of_birth": date(1988, 11, 8),
        "time_of_birth": time(9, 45, 0),
        "place_of_birth": {"latitude": 22.5726, "longitude": 88.3639},  # Kolkata
        "timezone": "Asia/Kolkata",
    }

    kundli1 = astrology_service.compute_kundli(birth_details)
    kundli2 = astrology_service.compute_kundli(birth_details)

    # Birth details should be identical
    assert kundli1["birth_details"]["date"] == kundli2["birth_details"]["date"]
    assert kundli1["birth_details"]["time"] == kundli2["birth_details"]["time"]

    # Planetary positions should be identical (same input = same output)
    planets1 = kundli1["planetary_positions"]
    planets2 = kundli2["planetary_positions"]

    for planet in planets1:
        if planet in planets2:
            # The planetary data should match
            assert planets1[planet]["sign"] == planets2[planet]["sign"]
            assert planets1[planet]["rashi"] == planets2[planet]["rashi"]


def test_compute_kundli_serializable() -> None:
    """Test that kundli output is JSON serializable."""
    import json

    birth_details = {
        "date_of_birth": date(1985, 7, 22),
        "time_of_birth": time(18, 20, 0),
        "place_of_birth": {"latitude": 13.0827, "longitude": 80.2707},  # Chennai
        "timezone": "Asia/Kolkata",
    }

    kundli = astrology_service.compute_kundli(birth_details)

    # Should be able to serialize to JSON without errors
    try:
        json_str = json.dumps(kundli)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Should be able to deserialize back
        kundli_restored = json.loads(json_str)
        assert isinstance(kundli_restored, dict)
        assert "planetary_positions" in kundli_restored
    except TypeError as e:
        raise AssertionError(f"Kundli data is not JSON serializable: {e}")
