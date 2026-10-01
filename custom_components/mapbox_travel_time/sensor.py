"""Sensor platform for Mapbox Travel Time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MapboxTravelConfigEntry
from .const import DOMAIN
from .coordinator import MapboxTravelCoordinator


@dataclass(frozen=True, kw_only=True)
class MapboxSensorDescription(SensorEntityDescription):
    """Description of a Mapbox Travel Time sensor."""

    value_fn: Any


SENSORS: tuple[MapboxSensorDescription, ...] = (
    MapboxSensorDescription(
        key="travel_time",
        translation_key="travel_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=1,
        icon="mdi:car-clock",
        value_fn=lambda data: data.route.duration_seconds / 60,
    ),
    MapboxSensorDescription(
        key="typical_time",
        translation_key="typical_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=1,
        icon="mdi:clock-outline",
        value_fn=lambda data: (
            data.route.typical_duration_seconds / 60
            if data.route.typical_duration_seconds is not None
            else None
        ),
    ),
    MapboxSensorDescription(
        key="traffic_delay",
        translation_key="traffic_delay",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        suggested_display_precision=1,
        icon="mdi:traffic-light",
        value_fn=lambda data: (
            data.route.traffic_delay_seconds / 60
            if data.route.traffic_delay_seconds is not None
            else None
        ),
    ),
    MapboxSensorDescription(
        key="distance",
        translation_key="distance",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        icon="mdi:map-marker-distance",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.route.distance_meters / 1000,
    ),
)


async def async_setup_entry(hass, entry: MapboxTravelConfigEntry, async_add_entities) -> None:
    """Set up Mapbox Travel Time sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        MapboxTravelTimeSensor(coordinator, entry, description)
        for description in SENSORS
    )


class MapboxTravelTimeSensor(CoordinatorEntity[MapboxTravelCoordinator], SensorEntity):
    """Representation of one Mapbox route metric."""

    entity_description: MapboxSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MapboxTravelCoordinator,
        entry: MapboxTravelConfigEntry,
        description: MapboxSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data["route_name"],
            manufacturer="Mapbox",
            model="Directions API (driving-traffic)",
        )

    @property
    def native_value(self):
        """Return current sensor value."""
        if self.coordinator.data is None:
            return None
        value = self.entity_description.value_fn(self.coordinator.data)
        return round(value, 1) if isinstance(value, float) else value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Add useful route metadata to the primary travel-time sensor."""
        if self.entity_description.key != "travel_time" or self.coordinator.data is None:
            return None

        data = self.coordinator.data
        return {
            "origin": data.origin.label,
            "destination": data.destination.label,
            "distance_km": round(data.route.distance_meters / 1000, 1),
            "typical_duration_min": (
                round(data.route.typical_duration_seconds / 60, 1)
                if data.route.typical_duration_seconds is not None
                else None
            ),
            "traffic_delay_min": (
                round(data.route.traffic_delay_seconds / 60, 1)
                if data.route.traffic_delay_seconds is not None
                else None
            ),
            "last_successful_update": data.updated_at.isoformat(),
            "profile": "mapbox/driving-traffic",
        }
