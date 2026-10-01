"""Mapbox Travel Time integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MapboxClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DESTINATION,
    CONF_ORIGIN,
    CONF_ROUTE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import MapboxTravelCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

type MapboxTravelConfigEntry = ConfigEntry[MapboxTravelCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MapboxTravelConfigEntry) -> bool:
    """Set up Mapbox Travel Time from a config entry."""
    session = async_get_clientsession(hass)
    client = MapboxClient(session, entry.data[CONF_ACCESS_TOKEN])
    coordinator = MapboxTravelCoordinator(hass, client, entry)

    _LOGGER.info(
        "[%s] Starting Mapbox Travel Time (%s -> %s, every %ss)",
        entry.data[CONF_ROUTE_NAME],
        entry.data[CONF_ORIGIN],
        entry.data[CONF_DESTINATION],
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MapboxTravelConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        _LOGGER.info("[%s] Unloaded", entry.data[CONF_ROUTE_NAME])
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: MapboxTravelConfigEntry) -> None:
    """Reload entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
