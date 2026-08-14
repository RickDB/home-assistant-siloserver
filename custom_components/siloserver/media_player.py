"""Stable now-playing media player for SiloServer."""

from datetime import datetime
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)

from .entity import SiloEntity


_SESSION_ATTRIBUTE_KEYS = (
    "username",
    "profile_name",
    "client_label",
    "client_name",
    "client_ip",
    "client_version",
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
    "target_resolution",
    "target_video_codec",
    "target_audio_codec",
    "target_bitrate_kbps",
    "transcode_audio",
    "transcode_hw_accel",
    "node_display_name",
    "reporting_node",
)


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse Silo's RFC 3339 timestamp."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _session_sort_key(session: dict[str, Any]) -> tuple[str, str]:
    """Keep the longest-running active session on the media-player card."""
    return (str(session.get("started_at") or ""), str(session.get("session_id") or ""))


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up one permanent server-level media player."""
    async_add_entities([SiloNowPlayingPlayer(entry.runtime_data, entry)])


class SiloNowPlayingPlayer(SiloEntity, MediaPlayerEntity):
    """Represent the longest-running active Silo playback session."""

    _attr_name = "Now playing"

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.unique_id}_now_playing"

    @property
    def session(self) -> dict[str, Any] | None:
        sessions = self.coordinator.data["sessions"]
        return min(sessions, key=_session_sort_key) if sessions else None

    @property
    def state(self) -> MediaPlayerState:
        if not self.session:
            return MediaPlayerState.IDLE
        if self.session.get("is_paused"):
            return MediaPlayerState.PAUSED
        return MediaPlayerState.PLAYING

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        if not self.session or not self.session.get("has_playback_control"):
            return MediaPlayerEntityFeature(0)
        return (
            MediaPlayerEntityFeature.PAUSE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.STOP
        )

    @property
    def media_title(self) -> str | None:
        if not self.session:
            return None
        if self.session.get("media_type") == "episode":
            return self.session.get("episode_name") or self.session.get("media_title")
        return self.session.get("media_title")

    @property
    def media_series_title(self) -> str | None:
        return self.session.get("series_name") if self.session else None

    @property
    def media_season(self) -> int | None:
        return self.session.get("season_number") if self.session else None

    @property
    def media_episode(self) -> int | None:
        return self.session.get("episode_number") if self.session else None

    @property
    def media_image_url(self) -> str | None:
        return self.session.get("poster_url") if self.session else None

    @property
    def media_content_type(self) -> MediaType | None:
        if not self.session:
            return None
        if self.session.get("media_type") == "episode":
            return MediaType.TVSHOW
        return MediaType.MOVIE

    @property
    def media_position(self) -> float | None:
        return self.session.get("position_seconds") if self.session else None

    @property
    def media_duration(self) -> int | None:
        return self.session.get("file_duration") if self.session else None

    @property
    def media_position_updated_at(self) -> datetime | None:
        return _parse_timestamp(self.session.get("updated_at")) if self.session else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.session:
            return {"active_sessions": 0}
        attributes = {
            key: self.session[key]
            for key in _SESSION_ATTRIBUTE_KEYS
            if self.session.get(key) not in (None, "")
        }
        attributes["active_sessions"] = len(self.coordinator.data["sessions"])
        return attributes

    async def _command(self, command: str) -> None:
        if not self.session:
            return
        await self.coordinator.client.async_control(
            self.session["session_id"], command
        )
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self._command("pause")

    async def async_media_play(self) -> None:
        await self._command("resume")

    async def async_media_stop(self) -> None:
        await self._command("stop")
