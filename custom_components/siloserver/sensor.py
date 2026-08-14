"""Sensors for SiloServer."""

import hashlib
from typing import Any

from homeassistant.components.sensor import SensorEntity

from .entity import SiloEntity, session_client_key


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


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up activity and per-client playback sensors."""
    coordinator = entry.runtime_data
    async_add_entities([SiloActivitySensor(coordinator, entry)])
    known: set[str] = set()

    def add_sessions() -> None:
        new = []
        for session in coordinator.data["sessions"]:
            client_key = session_client_key(session)
            if client_key in known:
                continue
            known.add(client_key)
            new.extend(
                (
                    SiloPlaybackMethodSensor(coordinator, entry, client_key),
                    SiloPlaybackUserSensor(coordinator, entry, client_key),
                    SiloPlaybackProfileSensor(coordinator, entry, client_key),
                )
            )
        if new:
            async_add_entities(new)

    add_sessions()
    entry.async_on_unload(coordinator.async_add_listener(add_sessions))


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
                        "username",
                        "profile_name",
                        "media_title",
                        "episode_name",
                        "series_name",
                        "season_number",
                        "episode_number",
                        "media_type",
                        "client_label",
                        "client_ip",
                        "play_method",
                        "video_decision",
                        "audio_decision",
                        "stream_bitrate_kbps",
                        "position_seconds",
                        "is_paused",
                    )
                }
                for session in self.coordinator.data["sessions"]
            ]
        }


class SiloSessionSensor(SiloEntity, SensorEntity):
    """Base sensor for one observed Silo client."""

    def __init__(self, coordinator, entry, client_key: str, suffix: str) -> None:
        super().__init__(coordinator, entry)
        self.client_key = client_key
        digest = hashlib.sha256(client_key.encode()).hexdigest()[:16]
        self._attr_unique_id = f"{entry.unique_id}_client_{digest}_{suffix}"

    @property
    def session(self) -> dict[str, Any] | None:
        return next(
            (
                session
                for session in self.coordinator.data["sessions"]
                if session_client_key(session) == self.client_key
            ),
            None,
        )

    @property
    def available(self) -> bool:
        return super().available and self.session is not None

    @property
    def client_name(self) -> str:
        session = self.session or {}
        return (
            session.get("client_label")
            or session.get("client_name")
            or "Playback session"
        )


class SiloPlaybackMethodSensor(SiloSessionSensor):
    """Playback method and detailed stream information for a Silo client."""

    def __init__(self, coordinator, entry, client_key: str) -> None:
        super().__init__(coordinator, entry, client_key, "playback_method")

    @property
    def name(self) -> str:
        return f"{self.client_name} playback method"

    @property
    def icon(self) -> str:
        method = _playback_method(self.session or {})
        if method == "Transcoding":
            return "mdi:movie-cog"
        if method == "Remuxing":
            return "mdi:movie-filter"
        return "mdi:movie-open-play"

    @property
    def native_value(self) -> str:
        return _playback_method(self.session or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        session = self.session or {}
        values = {
            "silo_username": session.get("username"),
            "silo_profile": session.get("profile_name"),
            "client": session.get("client_label") or session.get("client_name"),
            "client_ip": session.get("client_ip"),
            "video_decision": session.get("video_decision"),
            "audio_decision": session.get("audio_decision"),
            "stream_bitrate_kbps": session.get("stream_bitrate_kbps"),
            "source_container": session.get("source_container"),
            "source_bitrate_kbps": session.get("source_bitrate_kbps"),
            "source_video_codec": session.get("source_video_codec"),
            "source_video_resolution": session.get("source_video_resolution"),
            "source_audio_codec": session.get("source_audio_codec"),
            "source_audio_channels": session.get("source_audio_channels"),
            "target_resolution": session.get("target_resolution"),
            "target_video_codec": session.get("target_video_codec"),
            "target_audio_codec": session.get("target_audio_codec"),
            "target_bitrate_kbps": session.get("target_bitrate_kbps"),
            "hardware_acceleration": session.get("transcode_hw_accel"),
            "transcode_node": session.get("node_display_name")
            or session.get("reporting_node"),
        }
        return {key: value for key, value in values.items() if value not in (None, "")}


class SiloPlaybackUserSensor(SiloSessionSensor):
    """Silo account currently playing on a client."""

    _attr_icon = "mdi:account"

    def __init__(self, coordinator, entry, client_key: str) -> None:
        super().__init__(coordinator, entry, client_key, "user")

    @property
    def name(self) -> str:
        return f"{self.client_name} user"

    @property
    def native_value(self) -> str:
        return (self.session or {}).get("username") or "Unknown"


class SiloPlaybackProfileSensor(SiloSessionSensor):
    """Silo profile currently playing on a client."""

    _attr_icon = "mdi:account-box"

    def __init__(self, coordinator, entry, client_key: str) -> None:
        super().__init__(coordinator, entry, client_key, "profile")

    @property
    def name(self) -> str:
        return f"{self.client_name} profile"

    @property
    def native_value(self) -> str:
        return (self.session or {}).get("profile_name") or "Default"
