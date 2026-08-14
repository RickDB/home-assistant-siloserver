"""Sensors for SiloServer."""

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers import entity_registry as er

from .entity import SiloEntity


_SESSION_ATTRIBUTE_KEYS = (
    "session_id",
    "username",
    "profile_name",
    "media_title",
    "episode_name",
    "series_name",
    "season_number",
    "episode_number",
    "media_type",
    "poster_url",
    "client_label",
    "client_name",
    "client_ip",
    "client_version",
    "client_build",
    "client_channel",
    "play_method",
    "video_decision",
    "audio_decision",
    "stream_bitrate_kbps",
    "source_container",
    "source_bitrate_kbps",
    "source_video_codec",
    "source_video_resolution",
    "source_audio_codec",
    "source_audio_channels",
    "source_audio_language",
    "source_audio_title",
    "source_audio_layout",
    "target_resolution",
    "target_video_codec",
    "target_audio_codec",
    "target_bitrate_kbps",
    "transcode_audio",
    "transcode_hw_accel",
    "node_display_name",
    "reporting_node",
    "position_seconds",
    "file_duration",
    "is_paused",
    "started_at",
    "updated_at",
)


def _playback_method(session: dict[str, Any]) -> str:
    """Return a readable playback method from Silo's component decisions."""
    video = str(session.get("video_decision") or "").lower()
    audio = str(session.get("audio_decision") or "").lower()
    method = str(session.get("play_method") or "").lower()

    if "transcod" in video or "transcod" in audio or "transcod" in method:
        return "Transcoding"
    if "remux" in video or "remux" in audio or "remux" in method:
        return "Remuxing"
    if method in {"direct", "directplay", "direct_play"} or "direct" in method:
        return "Direct play"
    return session.get("play_method") or "Unknown"


def _session_attributes(session: dict[str, Any]) -> dict[str, Any]:
    """Return useful, populated attributes for one active session."""
    attributes = {
        key: session[key]
        for key in _SESSION_ATTRIBUTE_KEYS
        if session.get(key) not in (None, "")
    }
    attributes["playback_method"] = _playback_method(session)
    return attributes


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up the stable Silo activity sensor."""
    registry = er.async_get(hass)
    library_prefix = f"{entry.unique_id}_library_"
    session_prefix = f"{entry.unique_id}_client_"

    # Versions before 0.4.0 registered transient sessions and libraries as
    # entities. Remove those obsolete entries once; active sessions now live as
    # attributes on the stable server activity sensor, following Plex's model.
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.unique_id.startswith((library_prefix, session_prefix)):
            registry.async_remove(registry_entry.entity_id)

    async_add_entities([SiloActivitySensor(entry.runtime_data, entry)])


class SiloActivitySensor(SiloEntity, SensorEntity):
    """Number and details of native Silo playback sessions."""

    _attr_name = "Active streams"
    _attr_icon = "mdi:play-network"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_active_streams"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["sessions"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose each live session without registering transient entities."""
        return {
            f"session_{index}": _session_attributes(session)
            for index, session in enumerate(
                self.coordinator.data["sessions"], start=1
            )
        }
