from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .api import SmsAlertApi, SmsAlertError
from .const import (
    CONF_API_KEY,
    CONF_CLEANUP_UTF8,
    CONF_USERNAME,
    DEFAULT_CLEANUP_UTF8,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_NAME = "smsalert"

# Service schema for notify.smsalert
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        # One phone number as string (recommended)
        vol.Optional("target"): cv.string,
        # Alternative: explicit phoneNumber
        vol.Optional("phoneNumber"): cv.string,
        # Optional per-call override
        vol.Optional("cleanupUtf8"): cv.boolean,
    }
)


def _pick_phone(call_data: dict[str, Any]) -> str | None:
    # Prefer explicit phoneNumber, fall back to target
    pn = call_data.get("phoneNumber") or call_data.get("phone_number")
    if isinstance(pn, str) and pn.strip():
        return pn.strip()
    tgt = call_data.get("target")
    if isinstance(tgt, str) and tgt.strip():
        return tgt.strip()
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,  # noqa: ARG001 - required by platform signature
) -> None:
    """Set up SMSAlert notify service from a config entry.

    We register a classic notify service: notify.smsalert
    This is compatible with automations/scripts and avoids the stricter
    notify.send_message schema (which does not allow custom fields in some HA versions).
    """
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.entry_id

    async def _handle(call: ServiceCall) -> None:
        data = entry.data
        opts = entry.options

        message: str = call.data.get("message", "")
        phone_number = _pick_phone(call.data)

        if not phone_number:
            _LOGGER.error(
                "SMSAlert: missing phone number. Provide service data: target: '+40...' (or phoneNumber: '+40...')"
            )
            return

        cleanup_utf8 = call.data.get(
            "cleanupUtf8",
            opts.get(CONF_CLEANUP_UTF8, data.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8)),
        )
        cleanup_utf8 = bool(cleanup_utf8)

        api = SmsAlertApi(hass=hass, username=data[CONF_USERNAME], api_key=data[CONF_API_KEY])

        try:
            await api.async_send_sms(
                phone_number=phone_number,
                message=message,
                cleanup_utf8=cleanup_utf8,
            )
        except SmsAlertError as err:
            _LOGGER.error("Failed sending SMS via SMSAlert: %s", err)

    # Register service under notify domain
    # NOTE: service name must be unique per domain; we assume one config entry.
    if not hass.services.has_service("notify", SERVICE_NAME):
        hass.services.async_register("notify", SERVICE_NAME, _handle, schema=SERVICE_SCHEMA)
    else:
        _LOGGER.warning(
            "notify.%s is already registered. If you configured SMSAlert twice, remove the extra entry.",
            SERVICE_NAME,
        )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the config entry."""
    # Remove the service only if this is the last configured entry.
    try:
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id, None)
            if not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN, None)
                if hass.services.has_service("notify", SERVICE_NAME):
                    hass.services.async_remove("notify", SERVICE_NAME)
    except Exception:  # pragma: no cover
        _LOGGER.exception("Error while unloading SMSAlert")
    return True
