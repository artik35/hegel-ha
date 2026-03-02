from __future__ import annotations

import asyncio
import socket

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    SUPPORTED_MODELS,
    CONF_MODEL,
    CONF_MODEL_PRESET,
    DEFAULT_MODEL_PRESET,
    MODEL_PRESETS,
    CONF_POWER_ON_VALUE,
    CONF_POWER_OFF_VALUE,
    CONF_SOURCES_MAP,
    CONNECT_TIMEOUT,
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    POLL_INTERVAL_CHOICES,
)


async def _async_can_connect(hass: HomeAssistant, host: str, port: int) -> bool:
    """Prosty test połączenia TCP (bez wysyłania komend). Safety-first."""
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=CONNECT_TIMEOUT)
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError, socket.gaierror):
        return False


class HegelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> HegelOptionsFlowHandler:
        return HegelOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            ok = await _async_can_connect(self.hass, host, port)
            if not ok:
                errors["base"] = "cannot_connect"
            else:
                preset = user_input[CONF_MODEL_PRESET]

                data = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_MODEL_PRESET: preset,
                }

                if preset != "CUSTOM":
                    data[CONF_SOURCES_MAP] = MODEL_PRESETS[preset]
                else:
                    data[CONF_SOURCES_MAP] = MODEL_PRESETS.get(DEFAULT_MODEL_PRESET, {})

                return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        model_preset_choices = list(MODEL_PRESETS.keys()) + ["CUSTOM"]
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_MODEL, default="H590"): vol.In(SUPPORTED_MODELS),
                vol.Required(CONF_MODEL_PRESET, default=DEFAULT_MODEL_PRESET): vol.In(model_preset_choices),
                # ECO / pseudo-standby: Twoje działające mapowanie
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class HegelOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={CONF_POLL_INTERVAL: user_input[CONF_POLL_INTERVAL]},
            )

        current = self._entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

        schema = vol.Schema(
            {
                vol.Required(CONF_POLL_INTERVAL, default=current): vol.In(POLL_INTERVAL_CHOICES),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
