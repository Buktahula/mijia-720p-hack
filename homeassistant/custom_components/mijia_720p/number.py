"""Number entity for Xiaomi Mijia 720p IR LED Brightness."""
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up number entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]

    async_add_entities([MijiaIrLedNumber(coordinator, client, host, entry)])

class MijiaIrLedNumber(CoordinatorEntity, NumberEntity):
    """IR LED brightness slider (0..255)."""

    _attr_has_entity_name = True
    _attr_name = "IR LED Brightness"
    _attr_icon = "mdi:brightness-6"
    _attr_native_min_value = 0
    _attr_native_max_value = 255
    _attr_native_step = 1

    def __init__(self, coordinator, client, host: str, entry: ConfigEntry):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._entry = entry
        self._attr_unique_id = f"mijia_{host}_ir_led_brightness"

    @property
    def native_value(self) -> float:
        camera = self.coordinator.data.get("camera", {})
        return float(camera.get("ir_led", 0))

    async def async_set_native_value(self, value: float) -> None:
        """Set IR LED brightness."""
        await self._client.async_set_ir_led(int(value))
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }
