"""Water pressure, nozzle position and water temperature levels."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ViCleanConfigEntry, protocol
from .device import ViCleanDevice
from .entity import ViCleanEntity

NUMBERS = (
    NumberEntityDescription(key="pump", translation_key="pump", icon="mdi:water-pump"),
    NumberEntityDescription(key="nozzle", translation_key="nozzle", icon="mdi:arrow-expand-horizontal"),
    NumberEntityDescription(key="temperature", translation_key="temperature", icon="mdi:thermometer-water"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ViCleanConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(ViCleanLevel(entry.runtime_data, desc) for desc in NUMBERS)


class ViCleanLevel(ViCleanEntity, NumberEntity, RestoreEntity):
    """Level 0-5, used for the next start and applied live while a program runs."""

    _attr_native_min_value = protocol.LEVEL_MIN
    _attr_native_max_value = protocol.LEVEL_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, device: ViCleanDevice, desc: NumberEntityDescription) -> None:
        super().__init__(device, desc.key)
        self.entity_description = desc

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state.replace(".", "", 1).isdigit():
            setattr(self.device.settings, self.entity_description.key, int(float(last.state)))

    @property
    def native_value(self) -> float:
        return getattr(self.device.settings, self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        await self.device.set_level(self.entity_description.key, int(value))
