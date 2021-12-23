"""SmsAlert platform for notify component."""
from http import HTTPStatus
import json
import logging

from aiohttp.hdrs import CONTENT_TYPE
import requests
import voluptuous as vol

from homeassistant.components.notify import PLATFORM_SCHEMA, BaseNotificationService
from homeassistant.const import (
    CONF_API_KEY,
    CONF_RECIPIENT,
    CONF_SENDER,
    CONF_USERNAME,
    CONTENT_TYPE_JSON,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

BASE_API_URL = "https://smsalert.mobi"
DEFAULT_SENDER = "hass"
TIMEOUT = 5

HEADERS = {CONTENT_TYPE: CONTENT_TYPE_JSON}


PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_RECIPIENT, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_SENDER, default=DEFAULT_SENDER): cv.string,
            }
        )
    )
)


def get_service(hass, config, discovery_info=None):
    """Get the SmsALert notification service."""
    return SmsAlertNotificationService(config)


class SmsAlertNotificationService(BaseNotificationService):
    """Implementation of a notification service for the SmsAlert service."""

    def __init__(self, config):
        """Initialize the service."""
        self.username = config[CONF_USERNAME]
        self.api_key = config[CONF_API_KEY]
        self.recipients = config[CONF_RECIPIENT]
        self.sender = config[CONF_SENDER]

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        ploads = {
	  'username' : self.username,
          'apiKey' : self.api_key,
          'tel' : ','.join(self.recipients),
          'message': message
	}

        api_url = f"{BASE_API_URL}/api/sms/sendBulk"
        resp = requests.post(
            api_url,
            timeout=TIMEOUT,
            data=ploads
        )
        if resp.status_code == HTTPStatus.OK:
            return

        obj = json.loads(resp.text)
        response_msg = obj.get("message")
        response_code = obj.get("errorCode")
        _LOGGER.error(
            "Error %s : %s (Code %s)", resp.status_code, response_msg, response_code
        )
