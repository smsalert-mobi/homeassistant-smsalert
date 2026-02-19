# SMSAlert Home Assistant Integration

Send SMS messages via **SMSAlert** from Home Assistant using a clean, UI-friendly service.

## Features
- UI setup (Config Flow)
- Uses SMSAlert API v2: `POST /api/v2/message/send`
- Global `cleanupUtf8` option (editable in UI)
- Service with full UI fields: `smsalert.send`

## Install (HACS)
1. Add this repository as a custom repository in HACS (category: Integration)
2. Install
3. Restart Home Assistant
4. Settings → Devices & Services → Add Integration → **SMSAlert**

## Usage

### Send SMS from an automation
```yaml
action:
  - service: smsalert.send
    data:
      phone_number: "+40720762291"
      message: "Hello from Home Assistant"
```

### Override cleanupUtf8 per call (optional)
```yaml
action:
  - service: smsalert.send
    data:
      phone_number: "+40720762291"
      message: "Diacritics test: ăâîșț"
      cleanupUtf8: false
```

## Notes
- Phone number is required per call (no stored recipients).
- `cleanupUtf8` default is configured from the integration UI (Options).

