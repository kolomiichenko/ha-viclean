"""Base entity for ViClean."""

from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER
from .device import ViCleanDevice


class ViCleanEntity(Entity):
    """Available while the toilet is seen by a connectable Bluetooth adapter or proxy."""

    _attr_has_entity_name = True

    def __init__(self, device: ViCleanDevice, key: str) -> None:
        self.device = device
        self._attr_translation_key = key
        self._attr_unique_id = f"{device.address}_{key}"
        self._attr_device_info = DeviceInfo(
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
            identifiers={(DOMAIN, device.address)},
            manufacturer=MANUFACTURER,
            model="ViClean",
            name=device.name,
        )

    @property
    def available(self) -> bool:
        return bluetooth.async_address_present(self.hass, self.device.address, connectable=True)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.device.add_listener(self.async_write_ha_state))
        # Refresh availability when the toilet disappears or shows up again.
        self.async_on_remove(
            bluetooth.async_track_unavailable(
                self.hass, self._on_bluetooth_change, self.device.address, connectable=True
            )
        )
        self.async_on_remove(
            bluetooth.async_register_callback(
                self.hass, self._on_bluetooth_change,
                bluetooth.BluetoothCallbackMatcher(address=self.device.address, connectable=True),
                bluetooth.BluetoothScanningMode.PASSIVE,
            )
        )

    @callback
    def _on_bluetooth_change(self, *_args: object) -> None:
        if self.available != self._last_available:
            self._last_available = self.available
            self.async_write_ha_state()

    _last_available: bool | None = None
