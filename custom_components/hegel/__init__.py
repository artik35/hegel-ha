from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS, CONF_HOST, CONF_PORT
from .coordinator import HegelCoordinator
from .hegel_client import HegelTcpClient


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if not data:
        return

    coordinator: HegelCoordinator = data["coordinator"]
    coordinator.update_poll_interval()
    await coordinator.async_request_refresh()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    client = HegelTcpClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    coordinator = HegelCoordinator(hass, entry, client)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:  # noqa: BLE001
        # Jeśli Hegel nie odpowiada / timeout — HA ma retry bez psucia platformy
        await client.async_close()
        raise ConfigEntryNotReady(str(e)) from e

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if data:
        try:
            await data["client"].async_close()
        except Exception:  # noqa: BLE001
            pass

    return ok
