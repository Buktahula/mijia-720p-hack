"""Button entities for Xiaomi Mijia 720p."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST, CONF_STEP_SIZE, DEFAULT_STEP_SIZE

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up button entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]
    step_size = entry.data.get(CONF_STEP_SIZE, DEFAULT_STEP_SIZE)

    entities = [
        # Directional PTZ
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Up", "mdi:arrow-up", "move", {"dir": "up", "step": step_size}),
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Down", "mdi:arrow-down", "move", {"dir": "down", "step": step_size}),
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Left", "mdi:arrow-left", "move", {"dir": "left", "step": step_size}),
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Right", "mdi:arrow-right", "move", {"dir": "right", "step": step_size}),
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Center", "mdi:image-filter-center-focus", "center"),
        MijiaPtzButton(coordinator, client, host, entry, "PTZ Calibrate", "mdi:cog-refresh", "calibrate"),
        # Presets (Go to)
        MijiaPtzButton(coordinator, client, host, entry, "Preset 1", "mdi:numeric-1-box", "preset", {"id": 1}),
        MijiaPtzButton(coordinator, client, host, entry, "Preset 2", "mdi:numeric-2-box", "preset", {"id": 2}),
        MijiaPtzButton(coordinator, client, host, entry, "Preset 3", "mdi:numeric-3-box", "preset", {"id": 3}),
        MijiaPtzButton(coordinator, client, host, entry, "Preset 4", "mdi:numeric-4-box", "preset", {"id": 4}),
        # Save Presets
        MijiaPtzButton(coordinator, client, host, entry, "Save Preset 1", "mdi:content-save-outline", "set_preset", {"id": 1}),
        MijiaPtzButton(coordinator, client, host, entry, "Save Preset 2", "mdi:content-save-outline", "set_preset", {"id": 2}),
        MijiaPtzButton(coordinator, client, host, entry, "Save Preset 3", "mdi:content-save-outline", "set_preset", {"id": 3}),
        MijiaPtzButton(coordinator, client, host, entry, "Save Preset 4", "mdi:content-save-outline", "set_preset", {"id": 4}),
        # System
        MijiaPtzButton(coordinator, client, host, entry, "Reboot", "mdi:restart", "reboot")
    ]

    async_add_entities(entities)

class MijiaPtzButton(CoordinatorEntity, ButtonEntity):
    """Button for PTZ and camera action."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, client, host: str, entry: ConfigEntry, name: str, icon: str, action: str, params: dict = None):
        super().__init__(coordinator)
        self._client = client
        self._host = host
        self._entry = entry
        self._action = action
        self._params = params or {}
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"mijia_{host}_{name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        if self._action == "move":
            await self._client.async_move(self._params["dir"], self._params.get("step", 3))
        elif self._action == "center":
            await self._client.async_center()
        elif self._action == "calibrate":
            await self._client.async_calibrate()
        elif self._action == "preset":
            await self._client.async_preset(self._params["id"])
        elif self._action == "set_preset":
            await self._client.async_set_preset(self._params["id"])
        elif self._action == "reboot":
            await self._client.async_reboot()

        await self.coordinator.async_request_refresh()
