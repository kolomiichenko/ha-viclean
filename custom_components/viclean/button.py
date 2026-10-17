"""Start/stop buttons."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ViCleanConfigEntry, protocol
from .device import ViCleanDevice
from .entity import ViCleanEntity


@dataclass(frozen=True, kw_only=True)
class ViCleanButtonDescription(ButtonEntityDescription):
    press: Callable[[ViCleanDevice], Awaitable[None]]


BUTTONS = (
    ViCleanButtonDescription(key="start_lady", icon="mdi:human-female",
                             press=lambda d: d.start(protocol.LADY)),
    ViCleanButtonDescription(key="start_gent", icon="mdi:human-male",
                             press=lambda d: d.start(protocol.GENT)),
    ViCleanButtonDescription(key="stop", icon="mdi:stop", press=lambda d: d.stop()),
    ViCleanButtonDescription(key="nozzle_maintenance", icon="mdi:spray-bottle",
                             press=lambda d: d.nozzle_maintenance(True)),
    ViCleanButtonDescription(key="nozzle_retract", icon="mdi:arrow-collapse-left",
                             press=lambda d: d.nozzle_maintenance(False)),
)


async def async_setup_entry(hass: HomeAssistant, entry: ViCleanConfigEntry,
                            async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities(ViCleanButton(entry.runtime_data, desc) for desc in BUTTONS)


class ViCleanButton(ViCleanEntity, ButtonEntity):
    entity_description: ViCleanButtonDescription

    def __init__(self, device: ViCleanDevice, desc: ViCleanButtonDescription) -> None:
        super().__init__(device, desc.key)
        self.entity_description = desc

    async def async_press(self) -> None:
        await self.entity_description.press(self.device)
