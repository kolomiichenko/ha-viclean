"""BLE connection to a ViClean shower toilet."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from . import protocol
from .const import (
    COMMAND_PAUSE,
    IDLE_DISCONNECT,
    NUS_RX,
    NUS_TX,
    PROGRAM_TIMEOUT,
    WRITE_PAUSE,
)

_LOGGER = logging.getLogger(__name__)


class ViCleanDevice:
    """Sends commands and keeps the wash settings and assumed program state."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self.settings = protocol.Settings()
        self.running: int | None = None  # LADY / GENT while a program runs
        self.last_reply: protocol.Reply | None = None
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._program_timer: asyncio.TimerHandle | None = None

    # --- state listeners ---------------------------------------------------

    @callback
    def add_listener(self, cb: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(cb)
        return lambda: self._listeners.remove(cb)

    @callback
    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    # --- commands ------------------------------------------------------------

    async def start(self, gender: int) -> None:
        await self._send(protocol.start_program(gender, self.settings))
        self.running = gender
        self._reset_program_timer()
        self._notify()

    async def stop(self) -> None:
        await self._send(protocol.break_program())
        self._program_finished()

    async def nozzle_maintenance(self, extend: bool = True) -> None:
        await self._send(protocol.nozzle_maintenance(extend))

    async def set_level(self, key: str, value: int) -> None:
        """Stores pump/nozzle/temperature, applies it at once if a program runs."""
        setattr(self.settings, key, value)
        if self.running is not None:
            build = {"pump": protocol.set_pump, "nozzle": protocol.set_nozzle,
                     "temperature": protocol.set_temperature}[key]
            await self._send(build(value))
        self._notify()

    async def set_flag(self, key: str, value: bool) -> None:
        """Stores oscillate/rotate/pulsate, toggles it at once if a program runs."""
        changed = getattr(self.settings, key) != value
        setattr(self.settings, key, value)
        if changed and self.running is not None:
            sub = {"oscillate": protocol.TOGGLE_OSCILLATION, "rotate": protocol.TOGGLE_ROTATION,
                   "pulsate": protocol.TOGGLE_PULSATION}[key]
            await self._send(protocol.toggle(sub))
        self._notify()

    # --- program state -------------------------------------------------------

    def _reset_program_timer(self) -> None:
        if self._program_timer:
            self._program_timer.cancel()
        self._program_timer = self.hass.loop.call_later(PROGRAM_TIMEOUT, self._program_finished)

    @callback
    def _program_finished(self) -> None:
        if self._program_timer:
            self._program_timer.cancel()
            self._program_timer = None
        self.running = None
        self._schedule_disconnect()
        self._notify()

    # --- BLE -----------------------------------------------------------------

    async def _send(self, data: bytes) -> None:
        async with self._lock:
            client = await self._connect()
            try:
                for part in protocol.chunks(data):
                    await client.write_gatt_char(NUS_RX, part, response=False)
                    await asyncio.sleep(WRITE_PAUSE)
                await asyncio.sleep(COMMAND_PAUSE)
            except BleakError as err:
                await self._disconnect()
                raise HomeAssistantError(f"{self.name}: {err}") from err
            _LOGGER.debug("%s: sent %s", self.name, data)
        self._schedule_disconnect()

    async def _connect(self) -> BleakClient:
        if self._client and self._client.is_connected:
            return self._client
        ble_device: BLEDevice | None = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise HomeAssistantError(f"{self.name} is out of Bluetooth range")
        try:
            client = await establish_connection(
                BleakClientWithServiceCache, ble_device, self.name,
                disconnected_callback=self._on_disconnect, max_attempts=3,
            )
            await client.start_notify(NUS_TX, self._on_data)
        except (BleakError, TimeoutError) as err:
            raise HomeAssistantError(f"Cannot connect to {self.name}: {err}") from err
        self._client = client
        return client

    def _on_data(self, _sender: object, data: bytearray) -> None:
        reply = protocol.parse_reply(bytes(data))
        _LOGGER.debug("%s: received %s -> %s", self.name, bytes(data), reply)
        if reply:
            self.last_reply = reply

    def _on_disconnect(self, _client: BleakClient) -> None:
        _LOGGER.debug("%s: disconnected", self.name)
        self._client = None
        if self.running is not None:
            # The toilet stops the program when the link drops.
            self.hass.loop.call_soon_threadsafe(self._program_finished)

    def _schedule_disconnect(self) -> None:
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
            self._disconnect_timer = None
        if self.running is None:
            self._disconnect_timer = self.hass.loop.call_later(
                IDLE_DISCONNECT, lambda: self.hass.async_create_task(self._disconnect())
            )

    async def _disconnect(self) -> None:
        if self.running is not None:
            return
        client, self._client = self._client, None
        if client and client.is_connected:
            await client.disconnect()

    async def shutdown(self) -> None:
        for timer in (self._disconnect_timer, self._program_timer):
            if timer:
                timer.cancel()
        self.running = None
        await self._disconnect()
