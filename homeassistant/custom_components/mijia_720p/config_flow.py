"""Config flow for Xiaomi Mijia 720p integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_STEP_SIZE,
    CONF_PORT,
    CONF_RTSP_PORT,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_RTSP_PORT,
    DEFAULT_STEP_SIZE
)

_LOGGER = logging.getLogger(__name__)

class Mijia720pConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi Mijia 720p."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            session = async_get_clientsession(self.hass)

            # Validate connection to camera REST API
            test_url = f"http://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}/api/motor.php?action=status"
            cgi_url = f"http://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}/api/motor.cgi?action=status"
            
            connected = False
            for url in (test_url, cgi_url):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            connected = True
                            break
                except Exception as err:
                    _LOGGER.debug("Connection test to %s failed: %s", url, err)

            if not connected:
                # If camera is powered on but PHP not yet ready, still check port 80
                try:
                    root_url = f"http://{host}:{user_input.get(CONF_PORT, DEFAULT_PORT)}/"
                    async with session.get(root_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            connected = True
                except Exception:
                    pass

            if not connected:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, f"{DEFAULT_NAME} ({host})"),
                    data=user_input
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Optional(CONF_STEP_SIZE, default=DEFAULT_STEP_SIZE): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): int
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
