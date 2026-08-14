# SiloServer for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Integration-18BCF2.svg)](https://www.home-assistant.io/)

A custom Home Assistant integration for [SiloServer](https://siloserver.org/),
built exclusively on Silo's native `/api/v1` API. Monitor active playback,
control supported sessions, inspect libraries, and start library scans from Home
Assistant.

> [!NOTE]
> This project is a custom integration, not a Home Assistant add-on. It connects
> Home Assistant to an existing SiloServer instance.

## Features

- UI-based setup with a Silo administrator account
- Active stream count and detailed playback diagnostics
- A media player entity for each active Silo client
- Native pause, resume, and stop controls for compatible clients
- Episode, season, series, and cover-art metadata
- A button to scan all enabled libraries
- Automatic Silo access-token refresh
- Local polling: no cloud service is required

Silo's native admin playback API currently supports pause, resume, and stop. It
does not expose previous or next commands, so the integration does not advertise
controls the server cannot execute.

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

### Manual

1. Download this repository.
2. Copy `custom_components/siloserver` to the `custom_components` directory in
   your Home Assistant configuration.
3. Restart Home Assistant.

The resulting path should be:

```text
<config>/custom_components/siloserver/
```

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
| **Active streams** sensor | Number of active sessions, with playback and client details as attributes |
| Session media players | One entity per observed Silo client, including playback state and media metadata |
| Playback method sensors | Direct play, remux, or transcode state for each client, with codecs, resolution, bitrate, hardware acceleration, and transcode-node details |
| Playback user sensors | Silo account currently playing on each client |
| Playback profile sensors | Silo profile currently playing on each client |
| **Scan all libraries** button | Starts a full scan of every enabled library |

Session media players are available only while their corresponding client has an
active playback session. Home Assistant retains previously discovered entities,
which become unavailable when no matching session is active.

## Why administrator access is required

Silo's native active-session listing, playback control, library listing, and scan
endpoints are protected administrator APIs. During setup, the supplied
credentials are exchanged for Silo access and refresh tokens. The password is
not stored by the integration; the tokens are stored in the Home Assistant
configuration entry.

## Troubleshooting

### The integration cannot connect

- Confirm the URL is reachable from the Home Assistant host or container.
- Include the URL scheme, for example `http://192.168.1.10:8090`.
- Verify that you are using the main Silo application port.
- For HTTPS, confirm that the certificate is trusted or adjust **Verify SSL
  certificate** when using a self-signed certificate.

### Authentication fails or administrator access is required

Sign in with a Silo account whose role is `admin`. A regular user cannot access
the session, control, and scan endpoints required by this integration.

### Playback controls are missing

Controls appear only when the active Silo session reports realtime playback
control support. Previous and next controls are unavailable because Silo's
native API does not currently expose those commands.

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
