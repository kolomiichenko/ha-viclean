"""Constants for the ViClean integration."""

DOMAIN = "viclean"
MANUFACTURER = "Villeroy & Boch"

# Nordic UART Service.
NUS_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # write to the device
NUS_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # notifications from the device

# The toilet stops a running program when Bluetooth disconnects, so the
# connection is kept open while a program may be running.
PROGRAM_TIMEOUT = 300  # seconds a program is assumed to run without a stop
IDLE_DISCONNECT = 30  # seconds to keep an idle connection open
WRITE_PAUSE = 0.05  # seconds between BLE writes of one frame
COMMAND_PAUSE = 0.1  # seconds after each frame
