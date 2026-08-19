from dataclasses import dataclass


@dataclass
class LinkConfig:
    name: str                  
    port: str                  
    baud: int
    role: str                  
    timeout: float = 0.01
    reconnect_interval: float = 2.0
    write_queue_size: int = 4000
    critical_put_timeout: float = 5.0


RELAY_PIXHAWK_PORT = "/dev/serial/by-id/usb-ArduPilot_fmuv3_2A001C000C51333239393630-if00"
RELAY_PIXHAWK_BAUD = 115200

GROUND_RADIO_PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0"
GROUND_RADIO_BAUD = 57600

MAIN_RADIO_PORT = "/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30I50E5-if00-port0"
MAIN_RADIO_BAUD = 57600

RELAY_SYSID = 1      # Relay Drone Pixhawk
MAIN_SYSID = 2       # Main Drone Pixhawk
GCS_SYSID = 255      # Ground Control Station

RELAY_COMPID = 1
MAIN_COMPID = 1
GCS_COMPID = 190

SYSID_TO_LINK = {
    RELAY_SYSID: "relay_pixhawk",
    MAIN_SYSID: "main_radio",
}

LINKS = [

    # Ground Station Telemetry Radio
    LinkConfig(
        name="ground_radio",
        port=GROUND_RADIO_PORT,
        baud=GROUND_RADIO_BAUD,
        role="gcs",
    ),

    # Relay Drone Pixhawk (USB)
    LinkConfig(
        name="relay_pixhawk",
        port=RELAY_PIXHAWK_PORT,
        baud=RELAY_PIXHAWK_BAUD,
        role="own_pixhawk",
    ),

    # Main Drone Telemetry Radio
    LinkConfig(
        name="main_radio",
        port=MAIN_RADIO_PORT,
        baud=MAIN_RADIO_BAUD,
        role="remote_drone",
    ),
]


NODE_NAME = "relay-drone-1"

CRITICAL_MESSAGE_TYPES = {
    "HEARTBEAT",
    "COMMAND_LONG",
    "COMMAND_INT",
    "COMMAND_ACK",
    "PARAM_REQUEST_READ",
    "PARAM_REQUEST_LIST",
    "PARAM_SET",
    "PARAM_VALUE",
    "MISSION_REQUEST",
    "MISSION_REQUEST_INT",
    "MISSION_REQUEST_LIST",
    "MISSION_COUNT",
    "MISSION_ITEM",
    "MISSION_ITEM_INT",
    "MISSION_ACK",
    "MISSION_CURRENT",
    "STATUSTEXT",
    "SET_MODE",
    "SYSTEM_TIME",
}


TELEMETRY_RATE_LIMITS_HZ = {
    "ATTITUDE": 5,
    "GLOBAL_POSITION_INT": 5,
    "VFR_HUD": 5,
    "SYS_STATUS": 2,
    "RC_CHANNELS": 2,
    "GPS_RAW_INT": 2,
    "LOCAL_POSITION_NED": 5,
    "SCALED_IMU": 2,
    "SCALED_IMU2": 2,
    "SERVO_OUTPUT_RAW": 2,
    "NAV_CONTROLLER_OUTPUT": 2,
    "BATTERY_STATUS": 1,
}

DEFAULT_TELEMETRY_RATE_HZ = 3
WIRED_RATE_MULTIPLIER = 4.0

DEDUP_CACHE_TTL_SEC = 2.0
DEDUP_CACHE_MAX_ENTRIES = 4096

SYSTEM_TIMEOUT_SEC = 10.0

ENABLE_ROUTING_LOG = True
MAX_ROUTING_QUEUE = 1000

DEBUG_PRINT_PACKETS = True  # Enable if needed