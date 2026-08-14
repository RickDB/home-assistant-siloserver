"""Buttons for SiloServer."""

import asyncio

from homeassistant.components.button import ButtonEntity

from .entity import SiloEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    async_add_entities([SiloScanAllButton(coordinator, entry)])


class SiloScanAllButton(SiloEntity, ButtonEntity):
    """Trigger a native full scan for every enabled Silo library."""

    _attr_icon = "mdi:folder-multiple-outline"
    _attr_name = "Scan all libraries"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_scan_all"

    async def async_press(self) -> None:
        library_ids = [
            library["id"]
            for library in self.coordinator.data["libraries"]
            if library.get("enabled", True)
        ]
        await asyncio.gather(
            *(self.coordinator.client.async_scan(library_id) for library_id in library_ids)
        )
        await self.coordinator.async_request_refresh()
