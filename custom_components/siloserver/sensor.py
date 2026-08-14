"""Sensors for SiloServer."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory

from .entity import SiloEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    entities = [SiloActivitySensor(coordinator, entry)]
    entities.extend(
        SiloLibrarySensor(coordinator, entry, library["id"])
        for library in coordinator.data["libraries"]
    )
    async_add_entities(entities)


class SiloActivitySensor(SiloEntity, SensorEntity):
    """Number of native Silo playback sessions."""

    _attr_name = "Active streams"
    _attr_icon = "mdi:play-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_active_streams"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["sessions"])

    @property
    def extra_state_attributes(self):
        return {
            "sessions": [
                {
                    key: session.get(key)
                    for key in (
                        "username", "profile_name", "media_title", "episode_name",
                        "series_name", "season_number", "episode_number", "media_type",
                        "client_label", "client_ip", "effective_play_method",
                        "play_method", "video_decision", "audio_decision",
                        "stream_bitrate_kbps", "position_seconds", "is_paused"
                    )
                }
                for session in self.coordinator.data["sessions"]
            ]
        }


class SiloLibrarySensor(SiloEntity, SensorEntity):
    """Status of a Silo library."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, library_id: int) -> None:
        super().__init__(coordinator, entry)
        self.library_id = library_id
        self._attr_unique_id = f"{entry.unique_id}_library_{library_id}"

    @property
    def library(self):
        return next(
            (x for x in self.coordinator.data["libraries"] if x["id"] == self.library_id),
            {},
        )

    @property
    def name(self) -> str:
        return f"Library {self.library.get('name', self.library_id)}"

    @property
    def native_value(self) -> str:
        return "enabled" if self.library.get("enabled") else "disabled"

    @property
    def extra_state_attributes(self):
        return {
            key: self.library.get(key)
            for key in (
                "type",
                "paths",
                "last_scanned_at",
                "scan_warning_code",
                "scan_warning_message",
            )
        }
