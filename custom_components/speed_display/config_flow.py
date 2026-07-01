"""Config flow for Speed Display."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import CONF_TOPIC_PREFIX, DOMAIN


class SpeedDisplayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            topic_prefix = str(user_input[CONF_TOPIC_PREFIX]).strip("/")
            if not topic_prefix:
                errors[CONF_TOPIC_PREFIX] = "required"
            else:
                await self.async_set_unique_id(topic_prefix)
                self._abort_if_unique_id_configured()
                data = dict(user_input)
                data[CONF_TOPIC_PREFIX] = topic_prefix
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Speed Display"): str,
                vol.Required(CONF_TOPIC_PREFIX, default="speed-display"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
