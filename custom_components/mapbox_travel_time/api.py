"""Async Mapbox Directions API client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import API_BASE, PROFILE, REQUEST_TIMEOUT


class MapboxError(Exception):
    """Base Mapbox integration error."""


class MapboxAuthError(MapboxError):
    """Authentication/authorization error."""


class MapboxRateLimitError(MapboxError):
    """Mapbox rate limit error."""


class MapboxRequestError(MapboxError):
    """Mapbox request or response error."""


@dataclass(slots=True)
class RouteResult:
    """Normalized route result."""

    duration_seconds: float
    typical_duration_seconds: float | None
    distance_meters: float
    code: str

    @property
    def traffic_delay_seconds(self) -> float | None:
        """Return live traffic delay against typical travel time."""
        if self.typical_duration_seconds is None:
            return None
        return max(0.0, self.duration_seconds - self.typical_duration_seconds)


class MapboxClient:
    """Small async client for Mapbox Directions API."""

    def __init__(self, session: ClientSession, access_token: str) -> None:
        self._session = session
        self._access_token = access_token

    async def async_route(
        self,
        origin_lat: float,
        origin_lon: float,
        destination_lat: float,
        destination_lon: float,
    ) -> RouteResult:
        """Fetch a traffic-aware route."""
        coordinates = (
            f"{origin_lon:.7f},{origin_lat:.7f};"
            f"{destination_lon:.7f},{destination_lat:.7f}"
        )
        url = f"{API_BASE}/{PROFILE}/{coordinates}"
        params = {
            "access_token": self._access_token,
            "overview": "false",
            "alternatives": "false",
            "steps": "false",
        }

        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(url, params=params)
                if response.status in (401, 403):
                    raise MapboxAuthError(
                        f"Mapbox authorization failed (HTTP {response.status})"
                    )
                if response.status == 429:
                    raise MapboxRateLimitError("Mapbox rate limit reached (HTTP 429)")
                response.raise_for_status()
                payload: dict[str, Any] = await response.json()
        except MapboxError:
            raise
        except TimeoutError as err:
            raise MapboxRequestError("Mapbox request timed out") from err
        except (ClientResponseError, ClientError, ValueError) as err:
            raise MapboxRequestError(f"Mapbox request failed: {err}") from err

        code = str(payload.get("code", ""))
        if code != "Ok":
            message = str(payload.get("message", "Unknown Mapbox error"))
            raise MapboxRequestError(f"Mapbox returned {code or 'error'}: {message}")

        routes = payload.get("routes") or []
        if not routes:
            raise MapboxRequestError("Mapbox returned no route")

        route = routes[0]
        try:
            duration = float(route["duration"])
            distance = float(route["distance"])
        except (KeyError, TypeError, ValueError) as err:
            raise MapboxRequestError("Mapbox response is missing route metrics") from err

        typical_raw = route.get("duration_typical")
        typical = None
        if typical_raw is not None:
            try:
                typical = float(typical_raw)
            except (TypeError, ValueError):
                typical = None

        return RouteResult(
            duration_seconds=duration,
            typical_duration_seconds=typical,
            distance_meters=distance,
            code=code,
        )
