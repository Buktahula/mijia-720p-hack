"""Home Assistant integration for Xiaomi Mijia 720p hacked camera."""
from datetime import timedelta
import logging
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_HOST,
    CONF_PORT,
    CONF_STEP_SIZE,
    DEFAULT_PORT,
    DEFAULT_STEP_SIZE
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)

class MijiaClient:
    """Async API client for Mijia 720p camera."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int = 80):
        self.session = session
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"
        self._use_cgi = False

    async def _request(self, endpoint: str, params: dict = None) -> dict:
        """Send request to camera API with automatic CGI fallback."""
        ext = "cgi" if self._use_cgi else "php"
        url = f"{self.base_url}/{endpoint}.{ext}"
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as res:
                if res.status == 200:
                    return await res.json(content_type=None)
        except Exception as err:
            if not self._use_cgi:
                # Try fallback to .cgi
                self._use_cgi = True
                url = f"{self.base_url}/{endpoint}.cgi"
                async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as res:
                    if res.status == 200:
                        return await res.json(content_type=None)
            _LOGGER.debug("Request to %s failed: %s", url, err)
        return {}

    async def async_get_data(self) -> dict:
        """Fetch all camera and system data."""
        motor = await self._request("motor", {"action": "status"})
        camera = await self._request("camera", {"action": "status"})
        system = await self._request("system", {"action": "info"})
        return {
            "motor": motor.get("motor", {}),
            "camera": camera.get("camera", {}),
            "system": system.get("system", {}),
            "presets": motor.get("presets", {})
        }

    async def async_move(self, direction: str, step: int = 3):
        return await self._request("motor", {"action": "move", "dir": direction, "step": step})

    async def async_goto(self, x: int, y: int):
        return await self._request("motor", {"action": "goto", "x": x, "y": y})

    async def async_center(self):
        return await self._request("motor", {"action": "center"})

    async def async_calibrate(self):
        return await self._request("motor", {"action": "calibrate"})

    async def async_preset(self, preset_id: int):
        return await self._request("motor", {"action": "preset", "id": preset_id})

    async def async_set_preset(self, preset_id: int):
        return await self._request("motor", {"action": "set_preset", "id": preset_id})

    async def async_set_night_mode(self, mode: str):
        return await self._request("camera", {"action": "night_mode", "mode": mode})

    async def async_set_ir_led(self, value: int):
        return await self._request("camera", {"action": "ir_led", "value": value})

    async def async_set_ir_cut(self, state: bool):
        return await self._request("camera", {"action": "ir_cut", "state": "on" if state else "off"})

    async def async_set_flip(self, state: bool):
        return await self._request("camera", {"action": "flip", "state": "on" if state else "off"})

    async def async_set_mirror(self, state: bool):
        return await self._request("camera", {"action": "mirror", "state": "on" if state else "off"})

    async def async_set_led(self, color: str, state: str):
        return await self._request("camera", {"action": "led", "color": color, "state": state})

    async def async_reboot(self):
        return await self._request("system", {"action": "reboot"})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xiaomi Mijia 720p from a config entry."""
    session = async_get_clientsession(hass)
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    client = MijiaClient(session, host, port)

    async def async_update_data():
        try:
            return await client.async_get_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Mijia camera: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"mijia_720p_{host}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator
    }

    # Register PTZ Services
    async def handle_ptz_move(call: ServiceCall):
        direction = call.data.get("direction", "up")
        step = call.data.get("step", entry.data.get(CONF_STEP_SIZE, DEFAULT_STEP_SIZE))
        await client.async_move(direction, step)
        await coordinator.async_request_refresh()

    async def handle_ptz_goto(call: ServiceCall):
        x = call.data.get("x", 16)
        y = call.data.get("y", 7)
        await client.async_goto(x, y)
        await coordinator.async_request_refresh()

    async def handle_ptz_center(call: ServiceCall):
        await client.async_center()
        await coordinator.async_request_refresh()

    async def handle_ptz_preset(call: ServiceCall):
        preset_id = call.data.get("id", 1)
        await client.async_preset(preset_id)
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "ptz_move", handle_ptz_move)
    hass.services.async_register(DOMAIN, "ptz_goto", handle_ptz_goto)
    hass.services.async_register(DOMAIN, "ptz_center", handle_ptz_center)
    hass.services.async_register(DOMAIN, "ptz_preset", handle_ptz_preset)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
