# SiloServer for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-18BCF2.svg)](https://www.home-assistant.io/)

A custom Home Assistant integration for [SiloServer](https://siloserver.org/),
built exclusively on Silo's native `/api/v1` API. Monitor active playback,
inspect detailed session information, and start library scans from Home
Assistant.

> [!NOTE]
> This project is a custom integration, not a Home Assistant add-on. It connects
> Home Assistant to an existing SiloServer instance.

## Features

- UI-based setup with a Silo administrator account
- Active stream count and detailed playback information
- Plex-style server activity sensor without transient session entities
- Direct play, remux, or transcode status for each active session
- Silo account and profile currently using each client
- Source and target codecs, resolution, bitrate, hardware acceleration, and node
  information
- Episode, season, series, and cover-art metadata
- A button to scan all enabled libraries
- Automatic Silo access-token refresh
- Local polling: no cloud service is required

Playback sessions are exposed as attributes on one stable server entity. Silo's
session API does not provide a persistent client machine identifier, so creating
an entity per observed session would leave stale entries in Home Assistant's
entity registry after playback ends or Home Assistant restarts.

## Requirements

- A running SiloServer instance
- A Silo administrator account
- Home Assistant with support for custom integrations
- HACS for the recommended installation method (optional)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Select **Integrations**.
3. Open the three-dot menu and select **Custom repositories**.
4. Add `https://github.com/rickdb/home-assistant-siloserver` and choose
   **Integration** as the category.
5. Search for **SiloServer**, select it, and choose **Download**.
6. Restart Home Assistant.

> [!NOTE]
> HACS may show its generic "icon not available" image for this repository. HACS
> currently does not display brand images bundled with custom integrations. The
> SiloServer brand image is included correctly and is used by supported Home
> Assistant integration pages after installation.

### Manual

1. Download this repository.
2. Copy `custom_components/siloserver` to the `custom_components` directory in
   your Home Assistant configuration.
3. Restart Home Assistant.

The resulting path should be:

```text
<config>/custom_components/siloserver/
```

### Updating

Use **Update** on the SiloServer download in HACS and restart Home Assistant. For
a manual installation, replace the complete `custom_components/siloserver`
directory with the new version before restarting.

Version `0.4.0` replaces transient session entities with the Plex-style stable
activity sensor. During startup, the integration removes obsolete session and
library entities from Home Assistant's entity registry.

## Configuration

1. In Home Assistant, go to **Settings → Devices & services**.
2. Select **Add integration** and search for **SiloServer**.
3. Enter the main Silo application URL, an administrator username, and the
   corresponding password.

The default URL is `http://silo-host:8090`. Use the main Silo application port,
not the Jellyfin compatibility port. Keep **Verify SSL certificate** enabled for
HTTPS servers with a trusted certificate; disable it only when connecting to a
server with a self-signed certificate.

## Entities

| Entity | Description |
| --- | --- |
| **Active streams** sensor | Number of active sessions, with each session's playback, user, profile, media, and client details exposed as attributes |
| **Scan all libraries** button | Starts a full scan of every enabled library |

The integration creates only stable server-level entities. Active playback
sessions appear and disappear as `session_1`, `session_2`, and subsequent
attributes without creating device or entity registry entries.

### Playback details

Open the **Active streams** sensor to see the `session_1`, `session_2`, and
subsequent attributes reported by Silo. Depending on the playback route and
available metadata, each session can include:

- Silo username and profile
- Client name and IP address
- Video and audio decisions
- Stream and source bitrate in kbit/s
- Source container, video codec, resolution, audio codec, and channel count
- Target resolution, codecs, and bitrate when transcoding
- Hardware-acceleration method and transcode node

Silo may omit attributes that do not apply to the current playback method.

## Why administrator access is required

Silo's native active-session listing, library listing, and scan endpoints are
protected administrator APIs. During setup, the supplied credentials are
exchanged for Silo access and refresh tokens. The password is not stored by the
integration; the tokens are stored in the Home Assistant configuration entry.

## Troubleshooting

### The integration cannot connect

- Confirm the URL is reachable from the Home Assistant host or container.
- Include the URL scheme, for example `http://192.168.1.10:8090`.
- Verify that you are using the main Silo application port.
- For HTTPS, confirm that the certificate is trusted or adjust **Verify SSL
  certificate** when using a self-signed certificate.

### Authentication fails or administrator access is required

Sign in with a Silo account whose role is `admin`. A regular user cannot access
the session and scan endpoints required by this integration.

### Playback details are unavailable

Start playback on a Silo client and allow up to 15 seconds for the integration's
next poll. Open **Developer tools → States**, select the **Active streams**
sensor, and inspect its `session_1` attribute. The session attribute disappears
after playback ends; the sensor itself remains available and returns `0`.

### HACS says "icon not available"

This is a known limitation in the current HACS frontend: it requests custom
integration icons from the legacy Home Assistant Brands CDN instead of using the
brand files shipped with the integration. It does not affect installation or
operation. Follow the upstream issue at
[hacs/integration#5223](https://github.com/hacs/integration/issues/5223).

## Support

Please use [GitHub Issues](https://github.com/rickdb/home-assistant-siloserver/issues)
for bug reports and feature requests. Include your Home Assistant version,
SiloServer version, relevant logs, and the steps needed to reproduce the issue.
Remove tokens, credentials, public IP addresses, and other sensitive information
before posting logs.

## Development

The integration lives in `custom_components/siloserver`. After making changes,
copy or link that directory into a Home Assistant development configuration and
restart Home Assistant. Python modules can be checked for syntax errors with:

```bash
python3 -m compileall custom_components/siloserver
```

Contributions are welcome through pull requests.
