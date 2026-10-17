"""Assumed program state (the toilet does not report it)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ViCleanConfigEntry, protocol
from .device import ViCleanDevice
from .entity import ViCleanEntity


async def async_setup_entry(hass: HomeAssistant, entry: ViCleanConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([ViCleanRunning(entry.runtime_data)])


class ViCleanRunning(ViCleanEntity, BinarySensorEntity):
    _attr_icon = "mdi:shower-head"

    def __init__(self, device: ViCleanDevice) -> None:
        super().__init__(device, "running")

    @property
    def is_on(self) -> bool:
        return self.device.running is not None

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        program = {protocol.LADY: "lady", protocol.GENT: "gent"}.get(self.device.running)
        return {"program": program}
