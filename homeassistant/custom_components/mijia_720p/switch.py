"""Switch entities for Xiaomi Mijia 720p."""
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up switch entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]

    entities = [
        MijiaGenericSwitch(coordinator, client, host, entry, "IR-Cut Filter", "mdi:camera-iris", "ir_cut"),
        MijiaGenericSwitch(coordinator, client, host, entry, "Vertical Flip", "mdi:flip-vertical", "flip"),
        MijiaGenericSwitch(coordinator, client, host, entry, "Horizontal Mirror", "mdi:flip-horizontal", "mirror"),
        MijiaGenericSwitch(coordinator, client, host, entry, "Blue Status LED", "mdi:led-on", "blue_led"),
        MijiaGenericSwitch(coordinator, client, host, entry, "Yellow Status LED", "mdi:led-outline", "yellow_led")
    ]

    async_add_entities(entities)

class MijiaGenericSwitch(CoordinatorEntity, SwitchEntity):
    """Switch for camera hardware toggles."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, client, host: str, entry: ConfigEntry, name: str, icon: str, feature: str):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._entry = entry
        self._feature = feature
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"mijia_{host}_{feature}"

    @property
    def is_on(self) -> bool:
        cam = self.coordinator.data.get("camera", {})
        val = cam.get(self._feature)
        if self._feature in ("ir_cut", "flip", "mirror"):
            return val in (1, "1", True, "on")
        elif self._feature in ("blue_led", "yellow_led"):
            return val == "on"
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn switch on."""
        if self._feature == "ir_cut":
            await self._client.async_set_ir_cut(True)
        elif self._feature == "flip":
            await self._client.async_set_flip(True)
        elif self._feature == "mirror":
            await self._client.async_set_mirror(True)
        elif self._feature == "blue_led":
            await self._client.async_set_led("blue", "on")
        elif self._feature == "yellow_led":
            await self._client.async_set_led("yellow", "on")

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn switch off."""
        if self._feature == "ir_cut":
            await self._client.async_set_ir_cut(False)
        elif self._feature == "flip":
            await self._client.async_set_flip(False)
        elif self._feature == "mirror":
            await self._client.async_set_mirror(False)
        elif self._feature == "blue_led":
            await self._client.async_set_led("blue", "off")
        elif self._feature == "yellow_led":
            await self._client.async_set_led("yellow", "off")

        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }
