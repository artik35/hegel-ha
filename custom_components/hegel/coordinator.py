from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CMD_INPUT_Q,
    CMD_MUTE_Q,
    CMD_POWER_Q,
    CMD_VOLUME_Q,
    DEFAULT_POLL_SECONDS,
)
from .hegel_client import HegelTcpClient, HegelState

_LOGGER = logging.getLogger(__name__)

_RE_POWER = re.compile(r"^-p\.(\d+)$")
_RE_MUTE = re.compile(r"^-m\.(\d+)$")
_RE_VOLUME = re.compile(r"^-v\.(\d+)$")
_RE_INPUT = re.compile(r"^-i\.(\d+)$")


def _parse_line_into_state(line: str, st: HegelState) -> None:
    line = (line or "").strip()

    m = _RE_POWER.match(line)
    if m:
        st.power = (int(m.group(1)) == 1)
        return

    m = _RE_MUTE.match(line)
    if m:
        st.mute = (int(m.group(1)) == 1)
        return

    m = _RE_VOLUME.match(line)
    if m:
        v = int(m.group(1))
        # safety clamp
        st.volume = max(0, min(100, v))
        return

    m = _RE_INPUT.match(line)
    if m:
        st.input_code = int(m.group(1))
        return


class HegelCoordinator(DataUpdateCoordinator[HegelState]):
    def __init__(self, hass: HomeAssistant, client: HegelTcpClient, poll_seconds: int | None = None) -> None:
        self._client = client
        self._consecutive_failures = 0

        super().__init__(
            hass,
            _LOGGER,
            name="hegel",
            update_interval=timedelta(seconds=poll_seconds or DEFAULT_POLL_SECONDS),
        )

    async def _async_update_data(self) -> HegelState:
        st = HegelState()
        try:
            # A) safety-first: 4 osobne zapytania (Twoje Node-RED robił co 15s osobno)
            for cmd in (CMD_POWER_Q, CMD_INPUT_Q, CMD_VOLUME_Q, CMD_MUTE_Q):
                line = await self._client.async_send_and_readline(cmd)
                _parse_line_into_state(line, st)
            self._consecutive_failures = 0
            return st
        except Exception as e:  # noqa: BLE001
            self._consecutive_failures += 1
            raise UpdateFailed(str(e)) from e

    @property
    def soft_available(self) -> bool:
        return self._consecutive_failures < 3

    async def async_close(self) -> None:
        await self._client.async_close()