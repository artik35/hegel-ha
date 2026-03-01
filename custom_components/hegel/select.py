from __future__ import annotations

import asyncio
import logging
import re

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_SOURCES_MAP, cmd_input
from .coordinator import HegelCoordinator
from .hegel_client import HegelState, HegelTcpClient

_LOGGER = logging.getLogger(__name__)


def _sorted_sources_map(sources_map: dict[str, str]) -> dict[int, str]:
    out: dict[int, str] = {}
    for key, value in (sources_map or {}).items():
        try:
            out[int(key)] = str(value)
        except Exception:  # noqa: BLE001
            continue
    return dict(sorted(out.items(), key=lambda item: item[0]))


class HegelSourceSelect(CoordinatorEntity[HegelCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:format-list-bulleted"

    def __init__(self, coordinator: HegelCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sources_map_raw: dict[str, str] = dict(entry.data.get(CONF_SOURCES_MAP, {}))
        self._sources_map: dict[int, str] = _sorted_sources_map(self._sources_map_raw)

        self._attr_name = "Source"
        self._attr_unique_id = f"{entry.entry_id}_source_select"

    @property
    def options(self) -> list[str]:
        return list(self._sources_map.values())

    @property
    def current_option(self) -> str | None:
        st: HegelState = self.coordinator.data
        if st is None or st.input_code is None:
            return None
        return self._sources_map.get(st.input_code)

    async def async_select_option(self, option: str) -> None:
        wanted = (option or "").strip().casefold()
        canonical = None
        for opt in self.options:
            if (opt or "").strip().casefold() == wanted:
                canonical = opt
                break
        if canonical is None:
            _LOGGER.warning("Invalid source option=%s; valid=%s", option, self.options)
            return

        code = None
        for key, value in self._sources_map.items():
            if str(value) == canonical:
                code = key
                break

        if code is None:
            _LOGGER.warning("Unknown source selected: %s", canonical)
            return
        client: HegelTcpClient = self.coordinator._client  # noqa: SLF001
        await client.async_send_only(cmd_input(code))

        for delay_s in (0.2, 0.4, 0.8, 1.2):
            await asyncio.sleep(delay_s)
            try:
                line = await client.async_send_and_readline("-i.?")
                match = re.match(r"^-i\.(\d+)$", line or "")
                if match and int(match.group(1)) == code:
                    st = self.coordinator.data if self.coordinator.data is not None else HegelState()
                    st.input_code = code
                    self.coordinator.async_set_updated_data(st)
                    break
            except Exception:  # noqa: BLE001
                pass

        await self.coordinator.async_request_refresh()

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data["hegel"][entry.entry_id]
    coordinator: HegelCoordinator = data["coordinator"]
    async_add_entities([HegelSourceSelect(coordinator, entry)])
