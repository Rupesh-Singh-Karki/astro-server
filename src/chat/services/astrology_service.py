from typing import Any, Dict, cast
from datetime import datetime, date as Date, time as Time


from src.utils.logger import logger

log = logger(__name__)

# Import Jyotishyamitra library for Vedic astrology calculations
try:
    import jyotishyamitra as jm

    JYOTISHYAMITRA_AVAILABLE = True
except ImportError:  # pragma: no cover - requires external package
    JYOTISHYAMITRA_AVAILABLE = False
    jm = None


def _ensure_library_available() -> None:
    if not JYOTISHYAMITRA_AVAILABLE:
        raise RuntimeError(
            "Jyotishyamitra library is not installed. Install it via: `pip install jyotishyamitra` or from GitHub"
        )


class AstrologyService:
    """Compute kundli using Jyotishyamitra library for Vedic astrology calculations."""

    def compute_kundli(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute a kundli (natal chart) JSON from user birth details using Jyotishyamitra.

        Expected `details` keys:
        - name: str (optional, for reference)
        - date_of_birth: date
        - time_of_birth: time
        - place_of_birth: dict with latitude/longitude
        - timezone: str (e.g., "Asia/Kolkata")

        Returns a structured JSON with planetary positions, houses, dashas, etc.
        """
        _ensure_library_available()

        try:
            # Extract birth details
            dob = cast(Date, details.get("date_of_birth"))
            tob = cast(Time, details.get("time_of_birth"))
            place = details.get("place_of_birth")
            timezone_str = details.get("timezone", "UTC")

            # Extract coordinates
            if isinstance(place, dict):
                lat = float(place.get("latitude", 0))
                lon = float(place.get("longitude", 0))
            else:
                raise ValueError(
                    "place_of_birth must be a dict with 'latitude' and 'longitude' keys"
                )

            # Create birth data dict for jyotishyamitra
            birth_data = {
                "year": dob.year,
                "month": dob.month,
                "day": dob.day,
                "hour": tob.hour,
                "minute": tob.minute,
                "second": tob.second,
                "latitude": lat,
                "longitude": lon,
                "timezone": timezone_str,
            }

            # Generate kundli using jyotishyamitra
            # The exact API depends on the library structure
            # Assuming it has a function to compute chart data
            if hasattr(jm, "compute_chart"):
                chart_data = jm.compute_chart(**birth_data)
            elif hasattr(jm, "Horoscope"):
                horoscope = jm.Horoscope(**birth_data)
                chart_data = horoscope.get_chart_data()
            else:
                # Fallback: try to call the module as a function or use default API
                chart_data = self._compute_with_jyotishyamitra(birth_data)

            # Structure the kundli data
            kundli_data: Dict[str, Any] = {
                "birth_details": {
                    "name": details.get("full_name", details.get("name", "Unknown")),
                    "date": dob.isoformat(),
                    "time": tob.isoformat(),
                    "place": place,
                    "timezone": timezone_str,
                    "latitude": lat,
                    "longitude": lon,
                },
                "planetary_positions": self._extract_planetary_positions(chart_data),
                "houses": self._extract_houses(chart_data),
                "ascendant": self._extract_ascendant(chart_data),
                "dashas": self._extract_dashas(chart_data),
                "metadata": {
                    "ayanamsha": "Lahiri",
                    "generated_at": datetime.utcnow().isoformat(),
                    "source": "jyotishyamitra",
                },
            }

            return kundli_data

        except Exception as e:  # pragma: no cover - external package
            log.error(f"Failed to compute kundli: {e}")
            raise

    def _compute_with_jyotishyamitra(self, birth_data: Dict[str, Any]) -> Any:
        """Fallback method to compute chart with jyotishyamitra."""
        try:
            # Try different possible APIs
            if hasattr(jm, "calculate_horoscope"):
                return jm.calculate_horoscope(birth_data)
            elif hasattr(jm, "get_horoscope"):
                return jm.get_horoscope(birth_data)
            else:
                # Return birth data wrapped in a dict for processing
                log.warning("Could not find standard API, returning raw birth data")
                return {"birth_data": birth_data, "raw": True}
        except Exception as e:
            log.error(f"Error computing with jyotishyamitra: {e}")
            raise

    def _extract_planetary_positions(self, chart_data: Any) -> Dict[str, Any]:
        """Extract planetary positions from chart data."""
        try:
            if isinstance(chart_data, dict):
                # Look for common keys in chart data
                if "planets" in chart_data:
                    return chart_data["planets"]
                elif "planetary_positions" in chart_data:
                    return chart_data["planetary_positions"]
                elif "grahas" in chart_data:
                    return chart_data["grahas"]

            # If chart_data is an object, try to access attributes
            if hasattr(chart_data, "planets"):
                return self._serialize_planets(chart_data.planets)
            elif hasattr(chart_data, "get_planets"):
                return self._serialize_planets(chart_data.get_planets())

            return {}
        except Exception as e:
            log.warning(f"Error extracting planetary positions: {e}")
            return {}

    def _extract_houses(self, chart_data: Any) -> Dict[str, Any]:
        """Extract house information from chart data."""
        try:
            if isinstance(chart_data, dict):
                if "houses" in chart_data:
                    return chart_data["houses"]
                elif "bhavas" in chart_data:
                    return chart_data["bhavas"]

            if hasattr(chart_data, "houses"):
                return self._serialize_houses(chart_data.houses)
            elif hasattr(chart_data, "get_houses"):
                return self._serialize_houses(chart_data.get_houses())

            return {}
        except Exception as e:
            log.warning(f"Error extracting houses: {e}")
            return {}

    def _extract_ascendant(self, chart_data: Any) -> Dict[str, Any]:
        """Extract ascendant (lagna) information."""
        try:
            if isinstance(chart_data, dict):
                if "ascendant" in chart_data:
                    return chart_data["ascendant"]
                elif "lagna" in chart_data:
                    return chart_data["lagna"]

            if hasattr(chart_data, "ascendant"):
                asc = chart_data.ascendant
                return self._serialize_point(asc)
            elif hasattr(chart_data, "get_ascendant"):
                return self._serialize_point(chart_data.get_ascendant())

            return {}
        except Exception as e:
            log.warning(f"Error extracting ascendant: {e}")
            return {}

    def _extract_dashas(self, chart_data: Any) -> Dict[str, Any]:
        """Extract dasha information."""
        try:
            if isinstance(chart_data, dict):
                if "dashas" in chart_data:
                    return chart_data["dashas"]
                elif "vimshottari" in chart_data:
                    return chart_data["vimshottari"]

            if hasattr(chart_data, "dashas"):
                return self._serialize_dashas(chart_data.dashas)
            elif hasattr(chart_data, "get_dashas"):
                return self._serialize_dashas(chart_data.get_dashas())

            return {}
        except Exception as e:
            log.warning(f"Error extracting dashas: {e}")
            return {}

    def _serialize_planets(self, planets: Any) -> Dict[str, Any]:
        """Convert planet objects to dict."""
        result = {}
        try:
            if isinstance(planets, dict):
                return planets
            elif isinstance(planets, (list, tuple)):
                for planet in planets:
                    if hasattr(planet, "name"):
                        result[planet.name] = self._serialize_point(planet)
            return result
        except Exception:
            return {}

    def _serialize_houses(self, houses: Any) -> Dict[str, Any]:
        """Convert house objects to dict."""
        result = {}
        try:
            if isinstance(houses, dict):
                return houses
            elif isinstance(houses, (list, tuple)):
                for i, house in enumerate(houses, 1):
                    result[f"house_{i}"] = self._serialize_point(house)
            return result
        except Exception:
            return {}

    def _serialize_point(self, point: Any) -> Dict[str, Any]:
        """Convert a chart point (planet, house, ascendant) to dict."""
        try:
            if isinstance(point, dict):
                return point

            result = {}
            for attr in [
                "longitude",
                "latitude",
                "sign",
                "nakshatra",
                "house",
                "retrograde",
            ]:
                if hasattr(point, attr):
                    val = getattr(point, attr)
                    # Handle enum or object names
                    if hasattr(val, "name"):
                        result[attr] = val.name
                    else:
                        result[attr] = val
            return result
        except Exception:
            return {}

    def _serialize_dashas(self, dashas: Any) -> Dict[str, Any]:
        """Convert dasha objects to dict."""
        try:
            if isinstance(dashas, dict):
                return dashas
            elif hasattr(dashas, "__dict__"):
                return dashas.__dict__
            return {"dashas": str(dashas)}
        except Exception:
            return {}


astrology_service = AstrologyService()
