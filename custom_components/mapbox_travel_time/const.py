"""Constants for Mapbox Travel Time."""

from datetime import timedelta

DOMAIN = "mapbox_travel_time"

CONF_ACCESS_TOKEN = "access_token"
CONF_ROUTE_NAME = "route_name"
CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_LOG_SUCCESS = "log_successful_updates"

DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 60
MAX_SCAN_INTERVAL = 3600
DEFAULT_LOG_SUCCESS = False

PROFILE = "mapbox/driving-traffic"
API_BASE = "https://api.mapbox.com/directions/v5"
REQUEST_TIMEOUT = 15

PLATFORMS = ["sensor"]

ATTR_TYPICAL_DURATION = "typical_duration"
ATTR_TRAFFIC_DELAY = "traffic_delay"
ATTR_DISTANCE = "distance"
ATTR_LAST_SUCCESSFUL_UPDATE = "last_successful_update"
ATTR_ORIGIN = "origin"
ATTR_DESTINATION = "destination"

LOGGER_NAME = f"custom_components.{DOMAIN}"


def update_interval(seconds: int) -> timedelta:
    """Return coordinator update interval."""
    return timedelta(seconds=seconds)
