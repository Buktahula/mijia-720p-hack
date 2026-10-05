"""Camera platform for Xiaomi Mijia 720p."""
import logging
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.components.ffmpeg import async_get_image
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST, CONF_RTSP_PORT, DEFAULT_RTSP_PORT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the camera platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]
    rtsp_port = entry.data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT)

    async_add_entities([MijiaCamera(coordinator, entry, host, rtsp_port)])

class MijiaCamera(CoordinatorEntity, Camera):
    """Representation of the Mijia 720p Camera."""

    _attr_has_entity_name = True
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, coordinator, entry: ConfigEntry, host: str, rtsp_port: int):
        super().__init__(coordinator)
        Camera.__init__(self)
        self._entry = entry
        self._host = host
        self._rtsp_port = rtsp_port
        self._attr_name = "Camera Stream"
        self._attr_unique_id = f"mijia_{host}_camera"
        self._rtsp_url = f"rtsp://{host}:{rtsp_port}/live/ch00_0"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360° (MJSXJ01CM)",
            "sw_version": "Hacked Firmware 1.0",
        }

    async def async_camera_image(self, width: int = None, height: int = None) -> bytes:
        """Capture image frame from RTSP stream using ffmpeg."""
        return await async_get_image(
            self.hass,
            self._rtsp_url,
            output_format="image/jpeg",
            extra_cmd="-rtsp_transport tcp",
            width=width,
            height=height
        )

    async def stream_source(self):
        """Return RTSP stream source."""
        return self._rtsp_url
