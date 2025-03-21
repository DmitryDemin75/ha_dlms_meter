"""Config flow for DLMS integration."""
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_SERIAL_PORT,
    CONF_DEVICE,
    CONF_QUERY_CODE,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_PARITY,
    CONF_STOPBITS,
    CONF_TIMEOUT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_STOPBITS,
    DEFAULT_TIMEOUT,
    DEFAULT_DEVICE,
    DEFAULT_QUERY_CODE,
    DEFAULT_SERIAL_PORT,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class DLMSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DLMS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("DLMS Config Flow started")
        errors = {}

        if user_input is not None:
            # Check if device is already configured
            if self._async_current_entries():
                return self.async_abort(reason="already_configured")

            # Validate required fields
            if not user_input.get(CONF_SERIAL_PORT):
                errors["base"] = "serial_port_required"
            if not user_input.get(CONF_QUERY_CODE):
                errors["base"] = "query_code_required"

            if not errors:
                return self.async_create_entry(
                    title=user_input.get(CONF_DEVICE, "DLMS Meter"),
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE, default="DLMS Meter"): str,
                    vol.Required(CONF_SERIAL_PORT, default=DEFAULT_SERIAL_PORT): str,
                    vol.Required(CONF_QUERY_CODE, default=DEFAULT_QUERY_CODE): str,
                    vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): int,
                    vol.Required(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): int,
                    vol.Required(CONF_PARITY, default=DEFAULT_PARITY): str,
                    vol.Required(CONF_STOPBITS, default=DEFAULT_STOPBITS): int,
                    vol.Required(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
                    vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): int,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_config)