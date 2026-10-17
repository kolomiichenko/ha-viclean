# ViClean Bluetooth protocol

## Transport

Nordic UART Service, `6e400001-b5a3-f393-e0a9-e50e24dcca9e`:

| Characteristic | UUID | Direction |
|---|---|---|
| RX | `6e400002-…` | write (without response) to the toilet |
| TX | `6e400003-…` | notifications from the toilet |

Frames longer than 20 bytes are written in 20-byte chunks (50 ms apart); the
app waits ~100 ms between frames. No pairing or handshake is needed.

## Frames

ASCII, Modbus-like:

```
: FFFF <function> <command> <data...> <lrc> \r\n
```

Every byte after `:` is two upper-case hex digits. The LRC is the XOR of all
ASCII characters between `:` and the LRC.

Commands use function `05`:

| Command | Data | Meaning |
|---|---|---|
| `8E` | flags, pump, nozzle, temperature | start program |
| `8F` | – | stop program |
| `7E` | level 0–5 | water pressure |
| `81` | level 0–5 | nozzle position |
| `85` | level 0–5 | water temperature (0 = cold) |
| `88` / `89` / `8D` | – | toggle oscillation / rotation / pulsation |
| `8A` | – | toggle warm water |
| `65` | – | toggle buzzer |
| `82` | `01 00` / `00 00` | nozzle maintenance: move out (no water) / back in |
| `70` / `71` / `72` | – | move nozzle CW / CCW / wiggle |

Start flags: bits 0–1 = program + 1 (1 = lady, 2 = rear), bit 2 = oscillate,
bit 3 = rotate, bit 4 = pulsate.

Example, lady wash with oscillation and pulsation, all levels 3:
`:FFFF058E15030303` + LRC + `\r\n`.

## Replies

The toilet acknowledges commands with the same framing, address `01`:

```
:01 05 8F 00 00 00 00 7A    stop acknowledged
:01 45 85 00 03 00 22 0E    temperature set to 3
```

A disconnect stops a running program.
