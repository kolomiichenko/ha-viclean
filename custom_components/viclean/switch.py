"""Oscillation, rotation and pulsation."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ViCleanConfigEntry
from .device import ViCleanDevice
from .entity import ViCleanEntity

SWITCHES = (
    SwitchEntityDescription(key="oscillate", translation_key="oscillate", icon="mdi:swap-horizontal"),
    SwitchEntityDescription(key="rotate", translation_key="rotate", icon="mdi:rotate-right"),
    SwitchEntityDescription(key="pulsate", translation_key="pulsate", icon="mdi:pulse"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ViCleanConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([*(ViCleanFlag(entry.runtime_data, desc) for desc in SWITCHES),
                        ViCleanService(entry.runtime_data)])


class ViCleanFlag(ViCleanEntity, SwitchEntity, RestoreEntity):
    """Used for the next start and toggled live while a program runs."""

    _attr_assumed_state = True

    def __init__(self, device: ViCleanDevice, desc: SwitchEntityDescription) -> None:
        super().__init__(device, desc.key)
        self.entity_description = desc

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in (STATE_ON, STATE_OFF):
            setattr(self.device.settings, self.entity_description.key, last.state == STATE_ON)

    @property
    def is_on(self) -> bool:
        return getattr(self.device.settings, self.entity_description.key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.set_flag(self.entity_description.key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.set_flag(self.entity_description.key, False)


class ViCleanService(ViCleanEntity, SwitchEntity):
    """Service position: the nozzle moves out without water for cleaning."""

    _attr_assumed_state = True
    _attr_icon = "mdi:wrench"

    def __init__(self, device: ViCleanDevice) -> None:
        super().__init__(device, "service")

    @property
    def is_on(self) -> bool:
        return self.device.nozzle_out

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.nozzle_maintenance(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.nozzle_maintenance(False)
