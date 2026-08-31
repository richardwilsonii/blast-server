# Blast Server Review

Reviewed: August 30, 2026
Host: `blast-server`

This is a read-only inventory of the server software and functionality found during inspection. No configuration was changed.

## System overview

- Debian GNU/Linux 13.5 (`trixie`), kernel 6.12
- Intel Core i3-2120, 2 cores / 4 threads
- 7.7 GiB RAM and approximately 8 GiB swap
- 432 GB ext4 system disk, approximately 32 GB used
- Approximately 1,803 Debian packages installed
- No Docker, Podman, Snap, or Flatpak workloads detected

## Application functionality

### Node-RED

Node-RED 4.1.11 is installed and enabled as a system service. The configured flows provide:

- BCA front-desk setup and wristband/scanner processing
- Scanner service administration
- Game 1 and Game 2 dashboards
- MQTT monitoring and messaging
- Server and Raspberry Pi monitoring
- BCA database browsing
- Automated backup management
- SQLite, serial-port, GPIO, email, audio, and scheduled-task integrations

Configured dashboard pages include Front Desk, Scanner Service, Game 1, Game 2 Server Receiver, MQTT Monitor, Database, Blast Server, and RPIMon.

Configured HTTP endpoints include:

- `POST /bca/api/frontdesk-scan`
- `GET /bca/api/frontdesk-last-scan`
- `POST /bca/api/frontdesk-create-player`
- `POST /bca/api/frontdesk-scanner-status`
- `GET /bca/api/frontdesk-scanner-status`
- `POST /bca/api/frontdesk-lookup`
- `POST /bca/api/scanner-service/action`
- `GET /bca/api/scanner-service/active`

### BCA application and database

A custom BCA application data directory exists at `/home/blasty/bca`. Its SQLite schema supports:

- Players, accounts, roles, and permissions
- Wristbands, scanners, and scan events
- Wallets, credits, holds, and transactions
- Reservations and game sessions
- Games, devices, doors, and configuration
- Scores and public leaderboards
- Payments and external integrations
- Alerts, audit logging, and backup tracking

Automated SQLite backups are present, with the latest observed backup dated August 30, 2026.

A custom system service runs the ACR122U front-desk NFC scanner bridge and is configured to restart automatically.

## Web and messaging services

### Nginx

- Nginx 1.26.3 is installed and enabled.
- The active configuration is the default HTTP site on port 80.
- No custom reverse proxy or production TLS virtual host was found.
- Apache runtime components are present, but Apache is not configured as the active web server.

### MQTT

- Eclipse Mosquitto 2.0.21 is installed and enabled.
- It is configured to listen on all interfaces on port 1883.
- Multiple Node-RED flows use MQTT input and output nodes.

## Data services

- PostgreSQL 17.10 is installed and enabled.
- A PostgreSQL 17 `main` cluster is configured on port 5432 with 100 maximum connections and 128 MB shared buffers.
- The custom BCA workload currently uses SQLite 3.46.1.

The restricted inspection environment reported the PostgreSQL cluster as down. This should be confirmed directly from the host because the inspection environment could not reliably observe host service or process state.

## Remote access and networking

- OpenSSH server is installed and enabled.
- Tailscale 1.102.2 is installed and enabled.
- XRDP is installed and enabled.
- TigerVNC is installed.
- A custom x11vnc service is enabled on port 5900.
- GNOME and XFCE desktop environments are installed.
- Samba file and printer sharing is enabled with the standard home and printer shares.
- CUPS printing and Avahi/mDNS discovery are enabled.
- PC/SC smart-card support is installed.

## Development and administration tools

- Node.js 22.22.3
- npm 10.9.8
- Python 3.13.5
- Git 2.47.3
- PostgreSQL client 17.10
- SQLite 3.46.1
- Aptly 1.6.1 package repository management
- Cron and system statistics collection
- Firefox ESR, LibreOffice, GNOME, and XFCE desktop applications

## Security observations

The following findings warrant attention:

1. UFW is installed but disabled. Its default inbound policy is `DROP`, but that policy is not active while UFW is disabled.
2. Mosquitto accepts anonymous connections and listens on all interfaces.
3. The x11vnc service uses `-nopw`, allowing VNC access without a VNC password if the port is reachable.
4. The default Nginx site does not provide production TLS.
5. Installed and enabled status was verifiable from packages and service links, but actual host-level listening ports and running-service state could not be reliably observed from the restricted inspection environment.

Recommended priorities are to protect or disable unauthenticated VNC, require MQTT authentication, enable a carefully scoped firewall, configure TLS where web access is exposed, and verify the live service/port state directly on the host.
