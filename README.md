# Villeroy & Boch ViClean for Home Assistant

Custom [Home Assistant](https://www.home-assistant.io/) integration that
controls a **Villeroy & Boch ViClean** shower toilet (Dusch-WC, washlet,
bidet toilet) over Bluetooth LE, locally, without the ViClean app or any cloud:
start and stop the lady and rear wash, set water temperature, pressure and
nozzle position, and use them in automations, scripts and dashboards.

Other ViClean models that work with the Villeroy & Boch *ViClean* app over
Bluetooth (they advertise as `ViClean…` with the Nordic UART service) will
probably work too; reports are welcome.

Tested with a **ViClean-I 100** (advertises as `ViClean-I 100 XXXXXXXX`) on
Home Assistant 2026.10 with the built-in Bluetooth adapter of a Raspberry Pi 3B+.

## Entities

| Entity | What it does |
|---|---|
| Start lady wash / Start rear wash | start a wash program with the settings below |
| Stop | stop the running program |
| Water pressure, Nozzle position, Water temperature | levels 0–5; used for the next start and applied at once while a program runs |
| Oscillation, Rotation, Pulsation | used for the next start and toggled at once while a program runs |
| Program running | assumed state: on after a start, off after Stop, a disconnect or 5 minutes |
| Extend nozzle (service) / Retract nozzle | move the nozzle out without water for cleaning, and back in |

Settings are kept by Home Assistant (restored after a restart) and sent with
every start, like the app does.

## Limitations

- The toilet does not report its state; only command acknowledgements come
  back. "Program running" and the switches are assumed states.
- The toilet stops a running program when the Bluetooth connection drops, so
  the integration keeps the connection open while a program runs and closes it
  30 s after the program ends.
- Bluetooth range: the adapter (or an
  [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html))
  must be close enough for a stable connection; around −80 dBm or better works
  best.
- Only one Bluetooth client can be connected at a time: close the ViClean app
  while Home Assistant sends commands, and vice versa.

## Install

**HACS:** add this repository as a custom repository (category *Integration*),
install *Villeroy & Boch ViClean*, restart Home Assistant.

**Manually:** copy `custom_components/viclean` to `<config>/custom_components/`
and restart Home Assistant.

The toilet is discovered over Bluetooth automatically, or add it under
*Settings → Devices & services → Add integration → Villeroy & Boch ViClean*.

## Development

```sh
make venv    # pytest + ruff in .venv
make test    # protocol tests, no Home Assistant needed
make lint
make deploy HA_HOST=user@host HA_CONFIG=~/homeassistant/config
```

The protocol is described in [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Credits

The protocol was reverse engineered by
[lordvampire/viclean-esp32-controller](https://github.com/lordvampire/viclean-esp32-controller)
(an ESP32 remote for ViClean); this integration is an independent
implementation based on that description and on captured replies.

Not affiliated with Villeroy & Boch. Use at your own risk.

## License

MIT, see [LICENSE](LICENSE).
