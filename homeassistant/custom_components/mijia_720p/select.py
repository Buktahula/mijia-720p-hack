"""Select entity for Xiaomi Mijia 720p Night Vision."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up night vision select entity."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]

    async_add_entities([MijiaNightModeSelect(coordinator, client, host, entry)])

class MijiaNightModeSelect(CoordinatorEntity, SelectEntity):
    """Night mode selector (auto, on, off)."""

    _attr_has_entity_name = True
    _attr_name = "Night Vision Mode"
    _attr_icon = "mdi:weather-night"
    _attr_options = ["auto", "on", "off"]

    def __init__(self, coordinator, client, host: str, entry: ConfigEntry):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._entry = entry
        self._attr_unique_id = f"mijia_{host}_night_mode"

    @property
    def current_option(self) -> str:
        camera = self.coordinator.data.get("camera", {})
        if camera.get("auto_night") == "on" or camera.get("night_mode_nvram") == "0":
            return "auto"
        elif camera.get("night_mode") == "1" or camera.get("night_mode_nvram") == "2":
            return "on"
        return "off"

    async def async_select_option(self, option: str) -> None:
        """Change night mode."""
        await self._client.async_set_night_mode(option)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }
