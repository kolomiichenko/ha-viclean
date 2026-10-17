"""ViClean Bluetooth protocol: frame encoding and decoding.

Pure Python, no Home Assistant imports, so it can be tested on its own.

Frames are ASCII, Modbus-like, sent over the Nordic UART Service:

    :FFFF <cmd> <sub> <data...> <lrc> \\r\\n

Every byte after ':' is written as two upper-case hex digits. The LRC is the
XOR of all ASCII characters between ':' and the LRC itself.
"""

from __future__ import annotations

from dataclasses import dataclass

ADDRESS = "FFFF"
WRITE_COIL = 0x05

START_PROGRAM = 0x8E
BREAK_PROGRAM = 0x8F
SET_NOZZLE_POSITION = 0x81
NOZZLE_MAINTENANCE = 0x82
SET_TEMPERATURE = 0x85
SET_WATER_PUMP = 0x7E
TOGGLE_OSCILLATION = 0x88
TOGGLE_ROTATION = 0x89
TOGGLE_PULSATION = 0x8D

LEVEL_MIN, LEVEL_MAX = 0, 5
CHUNK_SIZE = 20  # bytes per BLE write

LADY, GENT = 0, 1


def lrc(text: str) -> int:
    value = 0
    for ch in text.encode("ascii"):
        value ^= ch
    return value


def frame(cmd: int, sub: int, data: bytes = b"") -> bytes:
    body = f"{ADDRESS}{cmd:02X}{sub:02X}{data.hex().upper()}"
    return f":{body}{lrc(body):02X}\r\n".encode("ascii")


def chunks(data: bytes, size: int = CHUNK_SIZE) -> list[bytes]:
    return [data[i : i + size] for i in range(0, len(data), size)]


def _level(value: int) -> int:
    if not LEVEL_MIN <= value <= LEVEL_MAX:
        raise ValueError(f"level must be {LEVEL_MIN}..{LEVEL_MAX}, got {value}")
    return value


@dataclass
class Settings:
    """Wash settings, sent with every program start."""

    pump: int = 3
    nozzle: int = 3
    temperature: int = 3
    oscillate: bool = True
    rotate: bool = True
    pulsate: bool = False


def start_program(gender: int, s: Settings) -> bytes:
    if gender not in (LADY, GENT):
        raise ValueError(f"unknown program {gender}")
    flags = ((gender + 1) & 0x03) | (s.oscillate << 2) | (s.rotate << 3) | (s.pulsate << 4)
    data = bytes([flags, _level(s.pump), _level(s.nozzle), _level(s.temperature)])
    return frame(WRITE_COIL, START_PROGRAM, data)


def break_program() -> bytes:
    return frame(WRITE_COIL, BREAK_PROGRAM)


def set_pump(level: int) -> bytes:
    return frame(WRITE_COIL, SET_WATER_PUMP, bytes([_level(level)]))


def set_nozzle(level: int) -> bytes:
    return frame(WRITE_COIL, SET_NOZZLE_POSITION, bytes([_level(level)]))


def set_temperature(level: int) -> bytes:
    return frame(WRITE_COIL, SET_TEMPERATURE, bytes([_level(level)]))


def toggle(sub: int) -> bytes:
    return frame(WRITE_COIL, sub)


def nozzle_maintenance() -> bytes:
    return frame(WRITE_COIL, NOZZLE_MAINTENANCE, bytes([0x01, 0x00]))


@dataclass
class Reply:
    address: int
    function: int
    command: int
    payload: bytes


def parse_reply(data: bytes) -> Reply | None:
    """Decodes a frame sent by the device, None if it is not a valid frame."""
    text = data.decode("ascii", errors="replace").strip()
    if not text.startswith(":") or len(text) < 9 or len(text) % 2 == 0:
        return None
    body, check = text[1:-2], text[-2:]
    try:
        if lrc(body) != int(check, 16):
            return None
        raw = bytes.fromhex(body)
    except ValueError:
        return None
    return Reply(address=raw[0], function=raw[1], command=raw[2], payload=raw[3:])
