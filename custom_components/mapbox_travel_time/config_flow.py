"""Config flow for Mapbox Travel Time."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MapboxAuthError, MapboxClient, MapboxError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DESTINATION,
    CONF_LOG_SUCCESS,
    CONF_ORIGIN,
    CONF_ROUTE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_LOG_SUCCESS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .helpers import LocationError, resolve_location


class MapboxTravelTimeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mapbox Travel Time."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Set up one traffic-aware route."""
        errors: dict[str, str] = {}

        if user_input is not None:
            route_name = user_input[CONF_ROUTE_NAME].strip()
            origin_value = user_input[CONF_ORIGIN].strip()
            destination_value = user_input[CONF_DESTINATION].strip()
            token = user_input[CONF_ACCESS_TOKEN].strip()

            try:
                origin = resolve_location(self.hass, origin_value)
                destination = resolve_location(self.hass, destination_value)
            except LocationError:
                errors["base"] = "invalid_location"
            else:
                client = MapboxClient(async_get_clientsession(self.hass), token)
                try:
                    await client.async_route(
                        origin.latitude,
                        origin.longitude,
                        destination.latitude,
                        destination.longitude,
                    )
                except MapboxAuthError:
                    errors[CONF_ACCESS_TOKEN] = "invalid_auth"
                except MapboxError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(route_name.casefold())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=route_name,
                        data={
                            CONF_ROUTE_NAME: route_name,
                            CONF_ACCESS_TOKEN: token,
                            CONF_ORIGIN: origin_value,
                            CONF_DESTINATION: destination_value,
                        },
                        options={
                            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                            CONF_LOG_SUCCESS: DEFAULT_LOG_SUCCESS,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_ROUTE_NAME): selector.TextSelector(),
                vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
                vol.Required(CONF_ORIGIN): selector.TextSelector(),
                vol.Required(CONF_DESTINATION): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Update an expired or invalid token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_ACCESS_TOKEN].strip()
            try:
                origin = resolve_location(self.hass, self._reauth_entry.data[CONF_ORIGIN])
                destination = resolve_location(self.hass, self._reauth_entry.data[CONF_DESTINATION])
                client = MapboxClient(async_get_clientsession(self.hass), token)
                await client.async_route(
                    origin.latitude,
                    origin.longitude,
                    destination.latitude,
                    destination.longitude,
                )
            except MapboxAuthError:
                errors[CONF_ACCESS_TOKEN] = "invalid_auth"
            except (MapboxError, LocationError):
                errors["base"] = "cannot_connect"
            else:
                new_data = {**self._reauth_entry.data, CONF_ACCESS_TOKEN: token}
                self.hass.config_entries.async_update_entry(self._reauth_entry, data=new_data)
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    )
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow."""
        return MapboxOptionsFlow()


class MapboxOptionsFlow(config_entries.OptionsFlow):
    """Handle route options."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage polling/logging options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=30,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                    vol.Required(
                        CONF_LOG_SUCCESS,
                        default=self.config_entry.options.get(
                            CONF_LOG_SUCCESS, DEFAULT_LOG_SUCCESS
                        ),
                    ): selector.BooleanSelector(),
                }
            ),
        )
