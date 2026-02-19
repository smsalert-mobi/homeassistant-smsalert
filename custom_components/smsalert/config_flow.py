from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_API_KEY,
    CONF_CLEANUP_UTF8,
    CONF_USERNAME,
    DEFAULT_CLEANUP_UTF8,
    DEFAULT_NAME,
    DOMAIN,
)


class SmsAlertConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            api_key = user_input[CONF_API_KEY].strip()
            cleanup_utf8 = bool(user_input.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8))

            await self.async_set_unique_id(f"{DOMAIN}:{username}")
            self._abort_if_unique_id_configured()

            # Put cleanup_utf8 in data (safe, and avoids update_entry in flow)
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_USERNAME: username,
                    CONF_API_KEY: api_key,
                    CONF_CLEANUP_UTF8: cleanup_utf8,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_CLEANUP_UTF8, default=DEFAULT_CLEANUP_UTF8): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmsAlertOptionsFlow(config_entry)


class SmsAlertOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_CLEANUP_UTF8: bool(user_input.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8))},
            )

        cur_cleanup = self.entry.options.get(
            CONF_CLEANUP_UTF8,
            self.entry.data.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8),
        )

        schema = vol.Schema({vol.Optional(CONF_CLEANUP_UTF8, default=cur_cleanup): bool})
        return self.async_show_form(step_id="init", data_schema=schema)
