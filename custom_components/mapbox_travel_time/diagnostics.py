"""Diagnostics support for Mapbox Travel Time."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MapboxTravelConfigEntry
from .const import CONF_ACCESS_TOKEN, CONF_DESTINATION, CONF_ORIGIN

TO_REDACT = {CONF_ACCESS_TOKEN, CONF_ORIGIN, CONF_DESTINATION}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MapboxTravelConfigEntry
) -> dict[str, Any]:
    """Return privacy-safe diagnostics."""
    coordinator = entry.runtime_data
    data = coordinator.data

    route_data: dict[str, Any] = {}
    if data is not None:
        route_data = {
            "duration_seconds": data.route.duration_seconds,
            "typical_duration_seconds": data.route.typical_duration_seconds,
            "traffic_delay_seconds": data.route.traffic_delay_seconds,
            "distance_meters": data.route.distance_meters,
            "response_code": data.route.code,
            "updated_at": data.updated_at.isoformat(),
        }

    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
        },
        "route": route_data,
    }
