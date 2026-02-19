from __future__ import annotations

import asyncio
import base64
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
    """Authentication error."""


class SmsAlertSendError(SmsAlertError):
    """Send error."""


@dataclass(slots=True)
class SmsAlertApi:
    hass: HomeAssistant
    username: str
    api_key: str

    async def async_send_sms(
        self,
        phone_number: str,
        message: str,
        cleanup_utf8: bool,
    ) -> None:

        if not phone_number:
            raise SmsAlertSendError("Missing phone number")

        if not message:
            raise SmsAlertSendError("Missing message")

        url = f"{BASE_API_URL}{SEND_V2_PATH}"
        session = async_get_clientsession(self.hass)

        # ✅ Proper Basic Auth header
        token = f"{self.username}:{self.api_key}"
        encoded = base64.b64encode(token.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }

        payload = {
            "phoneNumber": phone_number,
            "message": message,
            "cleanupUtf8": cleanup_utf8,
        }

        try:
            async with asyncio.timeout(TIMEOUT):
                response = await session.post(url, json=payload, headers=headers)
                text = await response.text()
        except TimeoutError as err:
            raise SmsAlertSendError("Timeout calling SMSAlert API") from err
        except ClientError as err:
            raise SmsAlertSendError("Network error calling SMSAlert API") from err

        if 200 <= response.status < 300:
            _LOGGER.debug("SMSAlert response: %s", text)
            return

        _LOGGER.error("SMSAlert API error %s: %s", response.status, text)

        if response.status in (401, 403):
            raise SmsAlertAuthError("Authentication failed")

        raise SmsAlertSendError(f"HTTP {response.status}")
