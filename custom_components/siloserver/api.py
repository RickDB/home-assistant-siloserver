"""Async client for SiloServer's native HTTP API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponse, ClientSession


class SiloError(Exception):
    """Base Silo API error."""


class SiloAuthenticationError(SiloError):
    """Authentication failed."""


class SiloConnectionError(SiloError):
    """The server could not be reached."""


class SiloApiClient:
    """Small client for the native /api/v1 Silo API."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        *,
        verify_ssl: bool = True,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self._session = session
        self.base_url = base_url.rstrip("/")
        self.verify_ssl = verify_ssl
        self.access_token = access_token
        self.refresh_token = refresh_token

    async def _request(
        self, method: str, path: str, *, retry_auth: bool = True, **kwargs: Any
    ) -> Any:
        headers = dict(kwargs.pop("headers", {}))
        headers.setdefault("User-Agent", "Home Assistant SiloServer")
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = await self._session.request(
                method,
                f"{self.base_url}/api/v1{path}",
                headers=headers,
                ssl=self.verify_ssl,
                **kwargs,
            )
        except ClientError as err:
            raise SiloConnectionError(str(err)) from err

        if response.status == 401 and retry_auth and self.refresh_token:
            response.release()
            await self.async_refresh_token()
            return await self._request(method, path, retry_auth=False, **kwargs)
        return await self._decode(response)

    @staticmethod
    async def _decode(response: ClientResponse) -> Any:
        if response.status in (401, 403):
            raise SiloAuthenticationError(f"Silo rejected the request ({response.status})")
        if response.status >= 400:
            try:
                body = await response.json()
                detail = body.get("message") or body.get("error")
            except (ValueError, ClientError):
                detail = await response.text()
            raise SiloError(detail or f"Silo API returned HTTP {response.status}")
        if response.status == 204:
            return None
        return await response.json()

    async def async_login(self, username: str, password: str) -> dict[str, Any]:
        data = await self._request(
            "POST",
            "/auth/login",
            retry_auth=False,
            json={"username": username, "password": password},
        )
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return data

    async def async_refresh_token(self) -> None:
        if not self.refresh_token:
            raise SiloAuthenticationError("No refresh token is available")
        data = await self._request(
            "POST",
            "/auth/refresh",
            retry_auth=False,
            json={"refresh_token": self.refresh_token},
        )
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    async def async_me(self) -> dict[str, Any]:
        return await self._request("GET", "/auth/me")

    async def async_sessions(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/admin/sessions")

    async def async_libraries(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/libraries")

    async def async_scan(self, library_id: int) -> None:
        """Start a full scan of one library."""
        await self._request("POST", "/scan", json={"library_id": library_id})

    async def async_control(self, session_id: str, command: str) -> None:
        await self._request(
            "POST", f"/admin/sessions/{session_id}/{command}", json={}
        )
