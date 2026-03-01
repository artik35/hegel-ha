# Hegel Integrated Amplifier (TCP)

## Overview

Home Assistant custom integration for controlling Hegel integrated amplifiers over TCP.
Tested on H590; should also work for H95, H120, H190, H390, and H590.

## Installation

### Manual

1. Copy `custom_components/hegel` into your Home Assistant config directory.
2. Restart Home Assistant.

### HACS Custom Repo

1. Open HACS.
2. Go to Integrations.
3. Add this repository as a Custom Repository.
4. Choose category: Integration.
5. Install `Hegel Integrated Amplifier (TCP)`.
6. Restart Home Assistant.

## Configuration

Use the UI config flow in Home Assistant and provide:
- host
- port
- model
- name

## Entities

- `media_player`
- `select` (source)

## Notes

- ECO is treated as pseudo-standby.
- State may lag by a few seconds.
