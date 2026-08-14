"""Config flow for SiloServer."""

from __future__ import annotations

import hashlib
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SiloApiClient, SiloAuthenticationError, SiloConnectionError, SiloError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_URL,
    CONF_USER_ID,
    CONF_VERIFY_SSL,
    DOMAIN,
)


class SiloServerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a native SiloServer connection."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            client = SiloApiClient(
                async_get_clientsession(self.hass),
                url,
                verify_ssl=user_input[CONF_VERIFY_SSL],
            )
            try:
                login = await client.async_login(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                user = login["user"]
                if user.get("role") != "admin":
                    errors["base"] = "admin_required"
                else:
                    await client.async_sessions()
                    unique_id = hashlib.sha256(url.lower().encode()).hexdigest()[:32]
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"SiloServer ({url.split('://')[-1]})",
                        data={
                            CONF_URL: url,
                            CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                            CONF_ACCESS_TOKEN: login[CONF_ACCESS_TOKEN],
                            CONF_REFRESH_TOKEN: login[CONF_REFRESH_TOKEN],
                            CONF_USER_ID: user["id"],
                        },
                    )
            except SiloAuthenticationError:
                errors["base"] = "invalid_auth"
            except SiloConnectionError:
                errors["base"] = "cannot_connect"
            except (SiloError, KeyError, TypeError):
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default="http://localhost:8090"): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_VERIFY_SSL, default=True): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
