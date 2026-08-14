"""Constants for the SiloServer integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "siloserver"
DEFAULT_PORT = 8090
DEFAULT_SCAN_INTERVAL = timedelta(seconds=15)
PLATFORMS = [Platform.SENSOR, Platform.MEDIA_PLAYER, Platform.BUTTON]

CONF_URL = "url"
CONF_VERIFY_SSL = "verify_ssl"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_USER_ID = "user_id"
