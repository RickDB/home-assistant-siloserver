"""SiloServer integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SiloApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_URL,
    CONF_VERIFY_SSL,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import SiloCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SiloServer from a config entry."""
    client = SiloApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_URL],
        verify_ssl=entry.data[CONF_VERIFY_SSL],
        access_token=entry.data[CONF_ACCESS_TOKEN],
        refresh_token=entry.data[CONF_REFRESH_TOKEN],
    )
    coordinator = SiloCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a SiloServer config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
