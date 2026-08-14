"""Media players for native Silo playback sessions."""

import hashlib
from datetime import datetime
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature
from homeassistant.components.media_player.const import MediaPlayerState, MediaType

from .entity import SiloEntity, session_client_key


_SESSION_ATTRIBUTE_KEYS = (
    "username",
    "profile_name",
    "client_ip",
    "client_name",
    "client_version",
    "client_build",
    "client_channel",
    "client_user_agent",
    "play_method",
    "video_decision",
    "audio_decision",
    "stream_bitrate_kbps",
    "reporting_node",
    "node_display_name",
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
    "requested_video_codec",
    "requested_video_resolution",
)


def _episode_title(session: dict[str, Any]) -> str | None:
    """Return the leaf title instead of repeating the series title."""
    if session.get("media_type") == "episode":
        return session.get("episode_name") or session.get("media_title")
    return session.get("media_title")


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse Silo's RFC 3339 update timestamp for HA position tracking."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    def add_sessions() -> None:
        new = []
        for session in coordinator.data["sessions"]:
            client_key = session_client_key(session)
            if client_key not in known:
                known.add(client_key)
                new.append(SiloSessionPlayer(coordinator, entry, client_key))
        if new:
            async_add_entities(new)

    add_sessions()
    entry.async_on_unload(coordinator.async_add_listener(add_sessions))


class SiloSessionPlayer(SiloEntity, MediaPlayerEntity):
    """A live native Silo playback session."""

    def __init__(self, coordinator, entry, client_key: str) -> None:
        super().__init__(coordinator, entry)
        self.client_key = client_key
        digest = hashlib.sha256(client_key.encode()).hexdigest()[:16]
        self._attr_unique_id = f"{entry.unique_id}_client_{digest}"

    @property
    def session(self):
        return next(
            (
                x
                for x in self.coordinator.data["sessions"]
                if session_client_key(x) == self.client_key
            ),
            None,
        )

    @property
    def available(self) -> bool:
        return super().available and self.session is not None

    @property
    def name(self) -> str:
        session = self.session or {}
        return session.get("client_label") or session.get("client_name") or "Playback session"

    @property
    def state(self):
        if not self.session:
            return MediaPlayerState.IDLE
        if self.session.get("is_paused"):
            return MediaPlayerState.PAUSED
        return MediaPlayerState.PLAYING

    @property
    def supported_features(self):
        if not self.session or not self.session.get("has_playback_control"):
            return MediaPlayerEntityFeature(0)
        return MediaPlayerEntityFeature.PAUSE | MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.STOP

    @property
    def media_title(self):
        return _episode_title(self.session) if self.session else None

    @property
    def media_series_title(self):
        return self.session.get("series_name") if self.session else None

    @property
    def media_season(self):
        return self.session.get("season_number") if self.session else None

    @property
    def media_episode(self):
        return self.session.get("episode_number") if self.session else None

    @property
    def media_image_url(self):
        return self.session.get("poster_url") if self.session else None

    @property
    def media_content_type(self):
        if not self.session:
            return None
        return MediaType.TVSHOW if self.session.get("media_type") == "episode" else MediaType.MOVIE

    @property
    def media_position(self):
        return self.session.get("position_seconds") if self.session else None

    @property
    def media_duration(self):
        return self.session.get("file_duration") if self.session else None

    @property
    def media_position_updated_at(self):
        return _parse_timestamp(self.session.get("updated_at")) if self.session else None

    @property
    def extra_state_attributes(self):
        if not self.session:
            return {}
        attributes = {
            key: self.session[key]
            for key in _SESSION_ATTRIBUTE_KEYS
            if self.session.get(key) not in (None, "")
        }
        attributes["silo_username"] = self.session.get("username")
        attributes["silo_profile"] = self.session.get("profile_name")
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
