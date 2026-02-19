from __future__ import annotations

import logging

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import SmsAlertApi, SmsAlertError
from .const import (
    CONF_API_KEY,
    CONF_CLEANUP_UTF8,
    CONF_USERNAME,
    DEFAULT_CLEANUP_UTF8,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    data = entry.data
    opts = entry.options

    entity = SmsAlertNotifyEntity(
        hass=hass,
        name=entry.title or DEFAULT_NAME,
        username=data[CONF_USERNAME],
        api_key=data[CONF_API_KEY],
        cleanup_utf8 = opts.get(
            CONF_CLEANUP_UTF8,
            data.get(CONF_CLEANUP_UTF8, DEFAULT_CLEANUP_UTF8),
        ),
    )
    async_add_entities([entity], update_before_add=False)


class SmsAlertNotifyEntity(NotifyEntity):
    """Notify entity for SMSAlert."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        username: str,
        api_key: str,
        cleanup_utf8: bool,
    ) -> None:
        self._attr_name = name
        self._api = SmsAlertApi(hass=hass, username=username, api_key=api_key)
        self._cleanup_utf8 = cleanup_utf8

    async def async_send_message(self, message: str, **kwargs) -> None:
        """
        Send a notification message.

        Expect exactly ONE destination provided by the automation.

        Supported ways to pass the number:
          1) target: "+40..."
          2) target: ["+40..."]   (must be a single item)
          3) data:
               phoneNumber: "+40..."
        """
        phone_number = None

        # Standard notify service supports "target"
        target = kwargs.get("target")
        if isinstance(target, str) and target.strip():
            phone_number = target.strip()
        elif isinstance(target, (list, tuple)):
            targets = [str(x).strip() for x in target if str(x).strip()]
            if len(targets) == 1:
                phone_number = targets[0]
            elif len(targets) > 1:
                _LOGGER.error("SMSAlert: only one phone number is allowed per notification")
                return

        # Also allow data.phoneNumber
        data = kwargs.get("data") or {}
        if phone_number is None:
            pn = data.get("phoneNumber") or data.get("phone_number")
            if isinstance(pn, str) and pn.strip():
                phone_number = pn.strip()

        if not phone_number:
            _LOGGER.error(
                "SMSAlert: missing phone number. Provide `target: '+40...'` or `data: { phoneNumber: '+40...' }`"
            )
            return

        # Allow per-call override of cleanupUtf8, but keep global default
        cleanup_utf8 = data.get("cleanupUtf8", self._cleanup_utf8)
        cleanup_utf8 = bool(cleanup_utf8)

        try:
            await self._api.async_send_sms(
                phone_number=phone_number,
                message=message,
                cleanup_utf8=cleanup_utf8,
            )
        except SmsAlertError as err:
            _LOGGER.error("Failed sending SMS via SMSAlert: %s", err)
