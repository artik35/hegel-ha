from __future__ import annotations

import asyncio
import logging

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_NAME,
    CONF_SOURCES_MAP,
    cmd_input,
    cmd_power,
    cmd_volume,
    cmd_mute_toggle,
)
from .coordinator import HegelCoordinator
from .hegel_client import HegelTcpClient, HegelState

_LOGGER = logging.getLogger(__name__)


def _invert_sources_map(sources_map: dict[str, str]) -> dict[int, str]:
    """Convert storage map {code_str: name} -> {code_int: name} (skip invalid)."""
    out: dict[int, str] = {}
    for k, v in (sources_map or {}).items():
        try:
            out[int(k)] = str(v)
        except Exception:  # noqa: BLE001
            continue
    return out


class HegelMediaPlayer(CoordinatorEntity[HegelCoordinator], MediaPlayerEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HegelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

        # { "1": "XLR1", ... } w storage
        self._sources_map_raw: dict[str, str] = dict(entry.data.get(CONF_SOURCES_MAP, {}))
        self._sources_map = _invert_sources_map(self._sources_map_raw)  # {1:"XLR1"}

        self._attr_name = entry.data.get(CONF_NAME, "Hegel")
        self._attr_unique_id = f"{entry.entry_id}_media_player"

        self._last_power: bool | None = None
        self._last_mute: bool | None = None
        self._last_volume: int | None = None
        self._last_input_code: int | None = None

        self._attr_supported_features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
        )

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.soft_available

    def _sync_cache_from_state(self) -> None:
        st: HegelState = self.coordinator.data
        if st is None:
            return
        if st.power is not None:
            self._last_power = st.power
        if st.mute is not None:
            self._last_mute = st.mute
        if st.volume is not None:
            self._last_volume = st.volume
        if st.input_code is not None:
            self._last_input_code = st.input_code

    @property
    def state(self) -> MediaPlayerState | None:
        self._sync_cache_from_state()
        st: HegelState = self.coordinator.data
        power = st.power if st is not None and st.power is not None else self._last_power
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def is_volume_muted(self) -> bool | None:
        self._sync_cache_from_state()
        st: HegelState = self.coordinator.data
        mute = st.mute if st is not None and st.mute is not None else self._last_mute
        return mute

    @property
    def volume_level(self) -> float | None:
        self._sync_cache_from_state()
        st: HegelState = self.coordinator.data
        volume = st.volume if st is not None and st.volume is not None else self._last_volume
        if volume is None:
            return None
        return max(0.0, min(1.0, volume / 100.0))

    @property
    def source_list(self) -> list[str]:
        return list(self._sources_map.values())

    @property
    def source(self) -> str | None:
        self._sync_cache_from_state()
        st: HegelState = self.coordinator.data
        input_code = st.input_code if st is not None and st.input_code is not None else self._last_input_code
        if input_code is None:
            return None
        return self._sources_map.get(input_code, f"Input {input_code}")

    async def async_turn_on(self) -> None:
        await self._send(cmd_power("1"))

    async def async_turn_off(self) -> None:
        await self._send(cmd_power("0"))

    async def async_set_volume_level(self, volume: float) -> None:
        percent = int(round(max(0.0, min(1.0, volume)) * 100))
        await self._send(cmd_volume(percent))

    async def async_mute_volume(self, mute: bool) -> None:
        st: HegelState = self.coordinator.data
        if st is None or st.mute is None:
            await self._send(cmd_mute_toggle())
            return
        if st.mute != mute:
            await self._send(cmd_mute_toggle())

    async def async_select_source(self, source: str) -> None:
        code = None
        wanted = (source or "").strip().casefold()
        for k, v in self._sources_map.items():
            if str(v).strip().casefold() == wanted:
                code = k
                break
        if code is None:
            _LOGGER.warning("Unknown source selected: %s", source)
            return
        client: HegelTcpClient = self.coordinator._client  # noqa: SLF001
        await client.async_send_only(cmd_input(code))

        import re

        for delay_s in (0.2, 0.4, 0.8, 1.2):
            await asyncio.sleep(delay_s)
            try:
                line = await client.async_send_and_readline("-i.?")
                match = re.match(r"^-i\.(\d+)$", line or "")
                if match and int(match.group(1)) == code:
                    st = self.coordinator.data if self.coordinator.data is not None else HegelState()
                    st.input_code = code
                    self.coordinator.async_set_updated_data(st)
                    self.async_write_ha_state()
                    break
            except Exception:  # noqa: BLE001
                pass

        await self.coordinator.async_request_refresh()

    async def _send(self, cmd: str) -> None:
        client: HegelTcpClient = self.coordinator._client  # noqa: SLF001
        await client.async_send_only(cmd)
        await asyncio.sleep(0.3)
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data["hegel"][entry.entry_id]
    coordinator: HegelCoordinator = data["coordinator"]
    async_add_entities([HegelMediaPlayer(coordinator, entry)])
