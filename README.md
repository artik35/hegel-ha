# Hegel Integrated Amplifier (TCP)

Home Assistant custom integration for controlling Hegel integrated amplifiers over TCP.

**Tested on:** H590  
**Should also work on (untested by author):** H95, H120, H190, H390, H590 (and similar models that expose the same TCP protocol).

> ⚠️ Disclaimer: Use at your own risk. The author(s) provide this integration “as is” without any warranty.
> Always verify behavior on your own setup. Audio equipment can be expensive—be cautious with automations.

---

## Installation

### Manual
1. Copy `custom_components/hegel` into your Home Assistant config directory.
2. Restart Home Assistant.

### HACS (Custom Repository)
1. Open HACS.
2. Go to **Integrations**.
3. Add this repository as a **Custom repository**.
4. Choose category: **Integration**.
5. Install **Hegel Integrated Amplifier (TCP)**.
6. Restart Home Assistant.

---

## Configuration

In Home Assistant:
1. Go to **Settings → Devices & services → Add integration**
2. Search for **Hegel Integrated Amplifier (TCP)**
3. Provide:
   - `host` (amplifier IP)
   - `port` (default: `50001`)
   - `model` (optional label)
   - `name` (device name in HA)

---

## Options

### Poll interval (`poll_interval`)
Controls how often (in seconds) Home Assistant polls the amplifier state over TCP (power / source / volume / mute).

- Lower values (e.g. **1–2s**) update the UI faster, but generate more TCP traffic and may increase the chance of short “Unavailable” flickers if the device occasionally misses a reply.
- Higher values (e.g. **5s**) reduce network traffic and usually improve stability, but state updates can lag by a few seconds.

Recommended starting point: **3s**. If you notice “Unavailable” flicker, try **5s**.

---

## Entities

- `media_player` (basic control + state)
- `select` (source selector)

**Note:** Source names are **case-sensitive** (must match exactly).

---

## Notes

- **ECO behavior:** turning the device “off” in Home Assistant typically switches the amplifier into **ECO/standby** mode (not a hard power cut).
- **State delays:** state changes (especially source) may lag by a few seconds depending on polling interval and device response timing.

---

## Troubleshooting

- If source selection doesn’t seem to work, verify the option name matches exactly (case-sensitive).
- If the device becomes temporarily unavailable, it usually recovers automatically on the next poll.

---

## How to report issues

When opening an issue, include:

- Amplifier model (e.g. H590, H390…).
- Home Assistant version.
- Integration version from `manifest.json` (`version`).
- IP/port setup (mask sensitive parts; confirm port `50001`).
- Exact steps to reproduce.
- Logs from **Settings → System → Logs**, filtered by `custom_components.hegel` (include ~20–50 lines).
- Confirm whether control works via service calls (**Developer Tools → Actions**) vs the UI card.
- Confirm whether any other Hegel control is running in parallel (Node-RED or other TCP clients).

