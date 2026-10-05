"""Constants for the Xiaomi Mijia 720p integration."""

DOMAIN = "mijia_720p"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_RTSP_PORT = "rtsp_port"
CONF_STEP_SIZE = "step_size"

DEFAULT_NAME = "Mijia 720p"
DEFAULT_PORT = 80
DEFAULT_RTSP_PORT = 554
DEFAULT_STEP_SIZE = 3

PLATFORMS = [
    "camera",
    "button",
    "select",
    "number",
    "switch",
    "sensor"
]
