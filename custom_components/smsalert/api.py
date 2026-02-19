from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_API_URL, SEND_V2_PATH, TIMEOUT

_LOGGER = logging.getLogger(__name__)


class SmsAlertError(Exception):
    """Base error for SMSAlert integration."""


class SmsAlertAuthError(SmsAlertError):
    """Auth/credential related error."""


class SmsAlertSendError(SmsAlertError):
    """Send related error."""


@dataclass(slots=True)
class SmsAlertApi:
    hass: HomeAssistant
    username: str
    api_key: str

    async def async_send_sms(self, phone_number: str, message: str, cleanup_utf8: bool) -> None:
        if not phone_number or not phone_number.strip():
            raise SmsAlertSendError("Missing phone_number")
        if message is None or str(message) == "":
            raise SmsAlertSendError("Missing message")

        url = f"{BASE_API_URL}{SEND_V2_PATH}"
        session = async_get_clientsession(self.hass)

        payload = {
            "username": self.username,
            "apiKey": self.api_key,
            "phoneNumber": phone_number.strip(),
            "message": message,
            "cleanupUtf8": bool(cleanup_utf8),
        }

        try:
            async with asyncio.timeout(TIMEOUT):
                resp = await session.post(url, json=payload)
                text = await resp.text()
        except TimeoutError as err:
            raise SmsAlertSendError("Timeout calling SMSAlert") from err
        except ClientError as err:
            raise SmsAlertSendError("Network error calling SMSAlert") from err

        if 200 <= resp.status < 300:
            return

        _LOGGER.error("SMSAlert HTTP %s: %s", resp.status, text)

        if resp.status in (401, 403):
            raise SmsAlertAuthError("Authentication failed")

        raise SmsAlertSendError(f"HTTP {resp.status}")
