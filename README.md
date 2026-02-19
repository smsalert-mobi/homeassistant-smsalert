# homeassistant-smsalert

This integration allows you to send SMS messages from you home assistant https://www.home-assistant.io/ instance.
Currently this is available only for users in Romania.

In order to use this integration you nee to create an account on https://smsalert.mobi/ and get you security token from settings page.


# Install via HACS (recommended)

Go to HACS -> custom repository (upper right corner) -> enter this repository URL https://github.com/smsalert-mobi/homeassistant-smsalert -> ADD

Click on "SMS Alert Notifications" -> Install this repository in HACS


# Install manually

Clone or copy the repository and copy the folder 'homeassistant-smsalert/custom_component/smsalert' into '/custom_components'

# Configuration

Add integration from autionation.

# Automations

Call service notify.smsalert and enter desired message.
