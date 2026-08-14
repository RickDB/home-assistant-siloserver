"""Data coordinator for SiloServer."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SiloApiClient, SiloError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SiloCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll native Silo library and playback state."""

    def __init__(
        self, hass, client: SiloApiClient, entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.title}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            sessions = await self.client.async_sessions()
            libraries = await self.client.async_libraries()
        except SiloError as err:
            raise UpdateFailed(str(err)) from err
        if (
            self.client.access_token != self.entry.data[CONF_ACCESS_TOKEN]
            or self.client.refresh_token != self.entry.data[CONF_REFRESH_TOKEN]
        ):
            self.hass.config_entries.async_update_entry(
                self.entry,
                data={
                    **self.entry.data,
                    CONF_ACCESS_TOKEN: self.client.access_token,
                    CONF_REFRESH_TOKEN: self.client.refresh_token,
                },
            )
        return {"sessions": sessions, "libraries": libraries}
