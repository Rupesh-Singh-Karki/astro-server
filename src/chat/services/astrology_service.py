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
                "astrological_context": {
                    "house_meanings": {
                        "1st_house": "Self, personality, physical appearance, health, overall life direction",
                        "2nd_house": "Wealth, family, speech, food, values, material possessions",
                        "3rd_house": "Courage, siblings, short journeys, communication, skills, efforts",
                        "4th_house": "Mother, home, emotions, education, vehicles, inner peace, property",
                        "5th_house": "Children, creativity, intelligence, romance, speculation, past karma",
                        "6th_house": "Enemies, diseases, debts, obstacles, service, daily work, competition",
                        "7th_house": "Marriage, partnerships, spouse, business partners, public relationships",
                        "8th_house": "Longevity, transformation, inheritance, occult, sudden events, mysteries",
                        "9th_house": "Fortune, father, religion, philosophy, higher learning, long journeys, dharma",
                        "10th_house": "Career, profession, fame, reputation, social status, authority, karma",
                        "11th_house": "Gains, income, friends, elder siblings, aspirations, fulfillment of desires",
                        "12th_house": "Loss, expenses, spirituality, foreign lands, isolation, liberation, bed pleasures",
                    },
                    "planet_significations": {
                        "Sun": "Soul, father, government, authority, vitality, ego, confidence",
                        "Moon": "Mind, mother, emotions, nurturing, intuition, mental peace",
                        "Mars": "Energy, courage, siblings, property, aggression, determination",
                        "Mercury": "Intelligence, communication, business, learning, analytical ability",
                        "Jupiter": "Wisdom, children, teacher, expansion, fortune, spirituality",
                        "Venus": "Love, beauty, luxury, arts, spouse, pleasure, material comforts",
                        "Saturn": "Discipline, delays, karma, hard work, responsibility, longevity",
                        "Rahu": "Desires, illusion, foreign elements, sudden gains, materialism",
                        "Ketu": "Spirituality, detachment, past life karma, liberation, losses",
                    },
                },
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
        """Compute chart with jyotishyamitra using the correct API."""
        try:
            # jyotishyamitra parameter order: name, gender, place, lon, lat, timezone, year, month, day, hour, min, sec
            log.info(
                f"Computing kundli for birth date {birth_data['year']}-{birth_data['month']}-{birth_data['day']}"
            )

            # Input birth data (note the parameter order!)
            birthdata = jm.input_birthdata(
                name="User",
                gender="Male",  # Default, can be made dynamic
                place="Birth Location",
                longitude=str(birth_data["longitude"]),
                lattitude=str(birth_data["latitude"]),
                timezone=birth_data.get("timezone", "UTC"),
                year=str(birth_data["year"]),
                month=str(birth_data["month"]),
                day=str(birth_data["day"]),
                hour=str(birth_data["hour"]),
                min=str(birth_data["minute"]),
                sec=str(birth_data["second"]),
            )

            # Generate astrological data
            jm.generate_astrologicalData(birthdata)

            # Return the jm module which now contains computed data
            return jm

        except Exception as e:
            log.error(f"Error computing with jyotishyamitra: {e}")
            raise

    def _extract_planetary_positions(self, chart_data: Any) -> Dict[str, Any]:
        """Extract planetary positions from chart data."""
        try:
            # jyotishyamitra stores data in chart_data.data.D1 dictionary
            if hasattr(chart_data, "data") and hasattr(chart_data.data, "D1"):
                d1_chart = chart_data.data.D1
                if isinstance(d1_chart, dict) and "planets" in d1_chart:
                    return self._make_serializable(d1_chart["planets"])

            return {}
        except Exception as e:
            log.warning(f"Error extracting planetary positions: {e}")
            return {}

    def _extract_houses(self, chart_data: Any) -> Dict[str, Any]:
        """Extract house information from chart data."""
        try:
            # jyotishyamitra stores house data in D1 chart
            if hasattr(chart_data, "data") and hasattr(chart_data.data, "D1"):
                d1_chart = chart_data.data.D1
                if isinstance(d1_chart, dict) and "houses" in d1_chart:
                    # Return houses directly without extra nesting
                    houses_data = self._make_serializable(d1_chart["houses"])
                    return houses_data if isinstance(houses_data, dict) else {}

            return {}
        except Exception as e:
            log.warning(f"Error extracting houses: {e}")
            return {}

    def _extract_ascendant(self, chart_data: Any) -> Dict[str, Any]:
        """Extract ascendant (lagna) information."""
        try:
            # jyotishyamitra stores ascendant in D1 chart
            if hasattr(chart_data, "data") and hasattr(chart_data.data, "D1"):
                d1_chart = chart_data.data.D1
                if isinstance(d1_chart, dict) and "ascendant" in d1_chart:
                    return self._make_serializable(d1_chart["ascendant"])

            return {}
        except Exception as e:
            log.warning(f"Error extracting ascendant: {e}")
            return {}

    def _extract_dashas(self, chart_data: Any) -> Dict[str, Any]:
        """Extract dasha information."""
        try:
            # jyotishyamitra has a dashas module
            if hasattr(chart_data, "dashas"):
                dashas_data = chart_data.dashas
                result = {}

                # Only extract simple types - avoid module objects
                for attr in dir(dashas_data):
                    if not attr.startswith("_") and attr not in [
                        "__loader__",
                        "__spec__",
                    ]:
                        val = getattr(dashas_data, attr, None)
                        # Only include serializable types
                        if val is not None and not callable(val):
                            # Check if it's a basic type or dict
                            if isinstance(
                                val, (str, int, float, bool, dict, list, tuple)
                            ):
                                result[attr] = self._make_serializable(val)
                            elif hasattr(val, "__dict__"):
                                # Try to convert to dict, but skip if it's a module/class
                                if (
                                    not isinstance(val, type)
                                    and type(val).__module__ != "builtins"
                                ):
                                    try:
                                        result[attr] = self._make_serializable(
                                            val.__dict__
                                        )
                                    except (AttributeError, TypeError):
                                        pass

                return result if result else {}

            return {}
        except Exception as e:
            log.warning(f"Error extracting dashas: {e}")
            return {}

    def _make_serializable(self, obj: Any) -> Any:
        """Recursively convert objects to JSON-serializable format."""
        from datetime import datetime, date, time

        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif hasattr(obj, "__dict__"):
            return self._make_serializable(obj.__dict__)
        else:
            # For any other type, try to convert to string
            return str(obj)

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
