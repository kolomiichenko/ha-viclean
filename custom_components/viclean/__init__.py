"""Villeroy & Boch ViClean shower toilet over Bluetooth LE."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .device import ViCleanDevice

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SWITCH]

type ViCleanConfigEntry = ConfigEntry[ViCleanDevice]


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

