"""Data update coordinator for Mapbox Travel Time."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from homeassistant.config_entries import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    MapboxAuthError,
    MapboxClient,
    MapboxRateLimitError,
    MapboxRequestError,
    RouteResult,
)
from .const import (
    CONF_DESTINATION,
    CONF_LOG_SUCCESS,
    CONF_ORIGIN,
    CONF_ROUTE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_LOG_SUCCESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    update_interval,
)
from .helpers import LocationError, ResolvedLocation, resolve_location

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MapboxTravelData:
    """Coordinator payload."""

    route: RouteResult
    origin: ResolvedLocation
    destination: ResolvedLocation
    updated_at: datetime


class MapboxTravelCoordinator(DataUpdateCoordinator[MapboxTravelData]):
    """Coordinate periodic route updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MapboxClient,
        entry,
    ) -> None:
        self.entry = entry
        self.client = client
        self.route_name = entry.data[CONF_ROUTE_NAME]
        seconds = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        self.log_success = bool(
            entry.options.get(CONF_LOG_SUCCESS, DEFAULT_LOG_SUCCESS)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {self.route_name}",
            update_interval=update_interval(seconds),
        )

    async def _async_update_data(self) -> MapboxTravelData:
        try:
            origin = resolve_location(self.hass, self.entry.data[CONF_ORIGIN])
            destination = resolve_location(self.hass, self.entry.data[CONF_DESTINATION])
        except LocationError as err:
            _LOGGER.warning(
                "[%s] Location resolution failed: %s",
                self.route_name,
                err,
            )
            raise UpdateFailed(str(err)) from err

        try:
            result = await self.client.async_route(
                origin.latitude,
                origin.longitude,
                destination.latitude,
                destination.longitude,
            )
        except MapboxAuthError as err:
            _LOGGER.error("[%s] Mapbox authentication failed", self.route_name)
            raise ConfigEntryAuthFailed(str(err)) from err
        except MapboxRateLimitError as err:
            _LOGGER.warning("[%s] %s", self.route_name, err)
            raise UpdateFailed(str(err)) from err
        except MapboxRequestError as err:
            _LOGGER.warning("[%s] Route update failed: %s", self.route_name, err)
            raise UpdateFailed(str(err)) from err

        updated_at = dt_util.utcnow()
        duration_min = result.duration_seconds / 60
        distance_km = result.distance_meters / 1000
        delay_min = (
            result.traffic_delay_seconds / 60
            if result.traffic_delay_seconds is not None
            else None
        )

        if self.log_success:
            _LOGGER.info(
                "[%s] Updated: %.1f min, %.1f km%s | %s -> %s",
                self.route_name,
                duration_min,
                distance_km,
                f", traffic delay +{delay_min:.1f} min" if delay_min is not None else "",
                origin.label,
                destination.label,
            )
        else:
            _LOGGER.debug(
                "[%s] Updated: %.1f min, %.1f km%s | %s -> %s",
                self.route_name,
                duration_min,
                distance_km,
                f", traffic delay +{delay_min:.1f} min" if delay_min is not None else "",
                origin.label,
                destination.label,
            )

        return MapboxTravelData(
            route=result,
            origin=origin,
            destination=destination,
            updated_at=updated_at,
        )
