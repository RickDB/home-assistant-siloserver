"""Shared SiloServer entity."""

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def session_client_key(session: dict[str, Any]) -> str:
    """Build a stable identity from fields exposed by Silo's native API."""
    client = (
        session.get("client_label")
        or session.get("client_name")
        or session.get("client_ip")
        or session["session_id"]
    )
    return f"{session.get('profile_id', '')}:{client}"


class SiloEntity(CoordinatorEntity):
    """Base entity attached to a Silo server."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=entry.title,
            manufacturer="Silo",
            model="SiloServer",
            configuration_url=coordinator.client.base_url,
        )
