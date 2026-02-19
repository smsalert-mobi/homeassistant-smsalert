from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .api import SmsAlertApi, SmsAlertError
from .const import (
    DOMAIN,
    SERVICE_SEND,
    CONF_USERNAME,
    CONF_API_KEY,
    CONF_CLEANUP_UTF8,
    DEFAULT_CLEANUP_UTF8,
)

DATA_API = "api"
DATA_ENTRIES = "entries"

SERVICE_SEND_SCHEMA = vol.Schema(
    {
        vol.Required("phone_number"): cv.string,
        vol.Required("message"): cv.string,
        vol.Optional("cleanupUtf8"): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_ENTRIES, set())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(DATA_ENTRIES, set())
    hass.data[DOMAIN][DATA_ENTRIES].add(entry.entry_id)

    api = SmsAlertApi(
        hass=hass,
        username=entry.data[CONF_USERNAME],
        api_key=entry.data[CONF_API_KEY],
    )

    # For simplicity (and your use-case), we assume a single configured entry.
    hass.data[DOMAIN][DATA_API] = api

    async def handle_send(call: ServiceCall) -> None:
        phone_number = str(call.data["phone_number"]).strip()
        message = call.data["message"]

        # Per-call override, else options, else entry.data, else default
        cleanup = call.data.get(
            "cleanupUtf8",
            entry.options.get(CONF_CLEANUP_UTF8, entry.data.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8)),
        )

        try:
            await api.async_send_sms(phone_number=phone_number, message=message, cleanup_utf8=bool(cleanup))
        except SmsAlertError as err:
            # Raising makes the UI show a clear failure
            raise RuntimeError(f"SMSAlert send failed: {err}") from err

    # Register service once
    if not hass.services.has_service(DOMAIN, SERVICE_SEND):
        hass.services.async_register(DOMAIN, SERVICE_SEND, handle_send, schema=SERVICE_SEND_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entries = hass.data.get(DOMAIN, {}).get(DATA_ENTRIES, set())
    entries.discard(entry.entry_id)

    # If last entry removed, unregister service
    if not entries:
        try:
            hass.services.async_remove(DOMAIN, SERVICE_SEND)
        except Exception:
            pass
        hass.data.pop(DOMAIN, None)

    return True
