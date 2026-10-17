"""Villeroy & Boch ViClean shower toilet over Bluetooth LE."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .device import ViCleanDevice

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SWITCH]

type ViCleanConfigEntry = ConfigEntry[ViCleanDevice]


SEND_RAW_SCHEMA = vol.Schema({
    vol.Required("function"): vol.All(vol.Coerce(int), vol.Range(0, 255)),
    vol.Required("command"): vol.All(vol.Coerce(int), vol.Range(0, 255)),
    vol.Optional("data", default=""): cv.string,
    vol.Optional("wait", default=1.5): vol.All(vol.Coerce(float), vol.Range(0.1, 10)),
})


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    async def send_raw(call: ServiceCall) -> ServiceResponse:
        """For protocol exploration: sends a frame, returns the replies."""
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("No ViClean configured")
        try:
            data = bytes.fromhex(call.data["data"].replace(" ", ""))
        except ValueError as err:
            raise HomeAssistantError(f"data must be hex: {err}") from err
        replies = await entries[0].runtime_data.send_raw(
            call.data["function"], call.data["command"], data, call.data["wait"]
        )
        return {"replies": replies}

    hass.services.async_register(DOMAIN, "send_raw", send_raw, schema=SEND_RAW_SCHEMA,
                                 supports_response=SupportsResponse.ONLY)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ViCleanConfigEntry) -> bool:
    address = entry.data[CONF_ADDRESS]
    entry.runtime_data = ViCleanDevice(hass, address, entry.title)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ViCleanConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.shutdown()
    return unloaded

