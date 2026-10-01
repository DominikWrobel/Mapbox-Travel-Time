"""Location helpers for Mapbox Travel Time."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant


class LocationError(ValueError):
    """Raised when a configured location cannot be resolved."""


@dataclass(slots=True)
class ResolvedLocation:
    """Resolved route endpoint."""

    latitude: float
    longitude: float
    label: str


def _validate_coordinates(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise LocationError("Latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise LocationError("Longitude must be between -180 and 180")


def parse_static_coordinates(value: str) -> tuple[float, float] | None:
    """Parse 'latitude,longitude'. Returns None if value is not coordinates."""
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 2:
        return None
    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError:
        return None
    _validate_coordinates(latitude, longitude)
    return latitude, longitude


def resolve_location(hass: HomeAssistant, value: str) -> ResolvedLocation:
    """Resolve an entity_id or static 'latitude,longitude' string."""
    static = parse_static_coordinates(value)
    if static is not None:
        latitude, longitude = static
        return ResolvedLocation(latitude, longitude, "static coordinates")

    state = hass.states.get(value)
    if state is None:
        raise LocationError(f"Entity '{value}' does not exist")

    latitude = state.attributes.get("latitude")
    longitude = state.attributes.get("longitude")
    if latitude is None or longitude is None:
        raise LocationError(
            f"Entity '{value}' does not provide latitude/longitude attributes"
        )

    try:
        lat_float = float(latitude)
        lon_float = float(longitude)
    except (TypeError, ValueError) as err:
        raise LocationError(
            f"Entity '{value}' has invalid latitude/longitude attributes"
        ) from err

    _validate_coordinates(lat_float, lon_float)
    label = state.attributes.get("friendly_name") or value
    return ResolvedLocation(lat_float, lon_float, str(label))
