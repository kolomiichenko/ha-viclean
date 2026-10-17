"""Protocol tests, run without Home Assistant: python -m pytest tests"""

import importlib.util
import pathlib
import sys

import pytest

_path = pathlib.Path(__file__).parent.parent / "custom_components/viclean/protocol.py"
_spec = importlib.util.spec_from_file_location("protocol", _path)
p = importlib.util.module_from_spec(_spec)
sys.modules["protocol"] = p
_spec.loader.exec_module(p)


def raw(hex_bytes: str) -> bytes:
    return bytes.fromhex(hex_bytes.replace(" ", ""))


# Replies captured from a real ViClean (temperature/pump/nozzle set to 3, nozzle 1).
CAPTURED = {
    "temp3": "3A 30 31 34 35 38 35 30 30 30 33 30 30 32 32 30 45 0D 0A",
    "pump3": "3A 30 31 34 35 37 45 30 30 30 33 30 30 30 30 37 31 0D 0A",
    "nozzle3": "3A 30 31 34 35 38 31 30 30 30 33 30 30 30 30 30 41 0D 0A",
    "nozzle1": "3A 30 31 34 35 38 31 30 30 30 31 46 46 46 45 30 42 0D 0A",
}


@pytest.mark.parametrize("name", CAPTURED)
def test_captured_replies_have_valid_lrc(name):
    reply = p.parse_reply(raw(CAPTURED[name]))
    assert reply is not None


def test_captured_reply_fields():
    reply = p.parse_reply(raw(CAPTURED["temp3"]))
    assert reply.command == p.SET_TEMPERATURE
    assert reply.payload[:2] == bytes([0x00, 0x03])


def test_frame_layout():
    f = p.set_temperature(4)
    assert f.startswith(b":FFFF058504") and f.endswith(b"\r\n")
    body = f[1:-4].decode()
    assert int(f[-4:-2], 16) == p.lrc(body)


def test_start_program_flags():
    s = p.Settings(pump=3, nozzle=3, temperature=3, oscillate=True, rotate=False, pulsate=True)
    assert p.start_program(p.LADY, s).startswith(b":FFFF058E15030303")
    s = p.Settings(oscillate=True, rotate=True, pulsate=False)
    assert p.start_program(p.GENT, s).startswith(b":FFFF058E0E030303")


def test_break_program():
    assert p.break_program().startswith(b":FFFF058F")


def test_levels_are_checked():
    with pytest.raises(ValueError):
        p.set_pump(6)
    with pytest.raises(ValueError):
        p.start_program(2, p.Settings())


def test_chunks():
    data = p.start_program(p.LADY, p.Settings())
    assert len(data) > 20
    parts = p.chunks(data)
    assert b"".join(parts) == data and all(len(c) <= 20 for c in parts)


def test_parse_rejects_garbage():
    assert p.parse_reply(b"hello") is None
    assert p.parse_reply(b":FFFF0585040\r\n") is None
    good = p.set_temperature(2)
    assert p.parse_reply(good[:-4] + b"00\r\n") is None


def test_nozzle_maintenance():
    assert p.nozzle_maintenance().startswith(b":FFFF05820100")
    assert p.nozzle_maintenance(False).startswith(b":FFFF05820000")
