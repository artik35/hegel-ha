# Hegel Integrated Amplifier (TCP)

Home Assistant custom integration for controlling Hegel integrated amplifiers over TCP (port 50001).

## Status / Compatibility

- Tested on: **H590**
- Should also work on: **H95, H120, H190, H390** (same IP control protocol), but not tested by the author.

## Important notes

- **Power OFF in Home Assistant = ECO/Standby on the amplifier.**
  Hegel units have a physical power button; IP control can only switch ECO/Standby.
- **State can lag by a few seconds.**
  Source/power changes may take a short moment to be reflected in Home Assistant.
- Use at your own risk. This project is provided “as is”, without warranty.

## Installation

### HACS (Custom repository)

1. Open HACS → Integrations.
2. Add this repository as a **Custom repository** (category: Integration).
3. Install **Hegel Integrated Amplifier (TCP)**.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/hegel` into your Home Assistant `config/custom_components/`.
2. Restart Home Assistant.

## Configuration

In Home Assistant:

1. Settings → Devices & services → Add integration
2. Search for **Hegel Integrated Amplifier (TCP)**
3. Provide:
   - IP address
   - Port (default: 50001)
   - Model
   - Name

## Entities

- `media_player` (basic control: on/off(ECO), volume, mute)
- `select` (source)

## Troubleshooting

- If source selection doesn’t seem to work, verify the option name matches exactly (case-sensitive).
- If the device becomes temporarily unavailable, it usually recovers automatically on the next poll.