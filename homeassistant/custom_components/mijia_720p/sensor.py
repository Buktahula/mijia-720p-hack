"""Sensor entities for Xiaomi Mijia 720p."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOST

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up sensor entities."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    host = entry.data[CONF_HOST]

    entities = [
        MijiaCoordSensor(coordinator, host, entry, "Pan Position", "mdi:pan-horizontal", "x"),
        MijiaCoordSensor(coordinator, host, entry, "Tilt Position", "mdi:pan-vertical", "y"),
        MijiaSystemSensor(coordinator, host, entry, "WiFi Signal", "mdi:wifi", "signal", "%"),
        MijiaSystemSensor(coordinator, host, entry, "SD Card Free", "mdi:micro-sd", "sd_free", "MB"),
        MijiaSystemSensor(coordinator, host, entry, "RAM Used", "mdi:memory", "mem_used", "MB")
    ]

    async_add_entities(entities)

class MijiaCoordSensor(CoordinatorEntity, SensorEntity):
    """Sensor for Pan / Tilt coordinates."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, host: str, entry: ConfigEntry, name: str, icon: str, axis: str):
        super().__init__(coordinator)
        self._host = host
        self._entry = entry
        self._axis = axis
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"mijia_{host}_{axis}_position"

    @property
    def native_value(self):
        motor = self.coordinator.data.get("motor", {})
        if self._axis == "x":
            return motor.get("horizontal", {}).get("x", 16)
        elif self._axis == "y":
            return motor.get("vertical", {}).get("y", 7)
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }

class MijiaSystemSensor(CoordinatorEntity, SensorEntity):
    """Sensor for camera system telemetry."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, host: str, entry: ConfigEntry, name: str, icon: str, metric: str, unit: str):
        super().__init__(coordinator)
        self._host = host
        self._entry = entry
        self._metric = metric
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"mijia_{host}_{metric}"

    @property
    def native_value(self):
        sys = self.coordinator.data.get("system", {})
        if self._metric == "signal":
            sig = sys.get("network", {}).get("signal", 0)
            try:
                return int(sig)
            except Exception:
                return 0
        elif self._metric == "sd_free":
            kb = sys.get("sdcard", {}).get("free_kb", 0)
            return round(kb / 1024, 1)
        elif self._metric == "mem_used":
            kb = sys.get("memory", {}).get("used_kb", 0)
            return round(kb / 1024, 1)
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._host)},
            "name": self._entry.title,
            "manufacturer": "Xiaomi / Grain Media",
            "model": "Mijia 720p 360°",
        }
