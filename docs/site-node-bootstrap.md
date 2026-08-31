# Blast Site-Node Bootstrap

Verified on August 30, 2026 against the live `blast-server` host.

## Architectural role

This host remains a Lost/Blast site executor and storage node. Central Trapped authorization, planning, portal, Operations data, software catalogue, audit history, and release authority remain in `richardwilsonii/trapped-infrastructure`.

No Trapped central executors, portal runtime, Rundeck instance, Operations database, release authority, credentials, or Cloudflare portal components were installed or copied here.

The central architecture repository was not readable using this host's GitHub SSH identity during bootstrap. Its repository boundary and the explicit constraints in the approved work order were preserved; direct architecture review remains required before implementing a site dispatcher or cross-tailnet protocol.

## Site-node prerequisites

Every required package was already installed and usable. No package was installed or reinstalled.

| Package | Installed version |
| --- | --- |
| `tailscale` | 1.102.2 |
| `openssh-server` | 10.0p1 Debian revision 7+deb13u4 |
| `openssh-client` | 10.0p1 Debian revision 7+deb13u4 |
| `rsync` | 3.4.1+ds1-5+deb13u4 |
| `python3` | 3.13.5-1 |
| `bash` | 5.2.37-2+b9 |
| `iproute2` | 6.15.0-1 |
| `iputils-ping` | 20240905-3 |
| `coreutils` | 9.7-3 |
| `sudo` | 1.9.16p2-3+deb13u2 |
| `git` | 2.47.3-0+deb13u1 |

Neither `nmap` nor `arp-scan` was installed.

## Site runtime filesystem

The preferred `/srv/trapped-site` could not be created non-interactively because filesystem administration requires a sudo password. The work order permits a documented equivalent when live constraints justify it, so the site root is:

```text
/home/blasty/trapped-site/
  backups/
  cache/
  queue/
  results/
  manifests/
  state/
  logs/
```

The root and every child directory are owned by `blasty:blasty` with mode `0750`. They are intentionally empty and contain no credentials. A future authenticated site-agent design may move the layout to `/srv/trapped-site` and assign a dedicated service account.

## SSH readiness

- OpenSSH server and client tooling are installed; the `ssh` service is active and enabled.
- The intended current management account is `blasty`, a member of the local `sudo` group.
- One authorized-key entry is configured for inbound access.
- The only explicit client host alias is GitHub, using strict existing host-key data and a dedicated local key.
- Outbound public-key SSH authentication to GitHub was verified without relaxing host-key checking.
- No SSH alias, known-host entry, or explicitly configured identity currently exists for the observed local LAN neighbor or the Pi-like `pt1` peers.
- Production Pis were not modified, arbitrary usernames were not attempted, and strict host-key checking was not disabled.
- `rsync` 3.4.1 is operational locally. Remote rsync-over-SSH was not attempted because no existing local-Pi SSH trust target was available.

Creating a secure `trapped-server` to `blast-server` management path remains blocked on the approved cross-tailnet transport and authentication design. No broad trust or private key copy was created.

## Tailscale boundary

- Tailscale is active, enabled, online, and joined to the existing Lost/Blast tailnet.
- Five tailnet peers were visible during inspection.
- The Pi-like `pt1` peer answered one bounded Tailscale ping through DERP; a direct connection was not established.
- The host advertises no subnet routes, is not an exit node, and was not moved into the Trapped tailnet.
- No Lost/Blast LAN subnet was exposed to another tailnet.

## LAN execution readiness

- Default LAN interface: `wlx1cbfce55b6fa`
- Host address during inspection: `192.168.1.23/24`
- Local subnet: `192.168.1.0/24`
- Default gateway: `192.168.1.1`
- `ip addr`, `ip route`, and `ip neigh` operate normally.
- One bounded ping to the gateway succeeded.
- The only other current neighbor entry, `192.168.1.165`, did not answer one bounded ping and had no existing SSH host-key entry.
- No unbounded scan was run and no production device was changed.

Local `ping`, SSH, and rsync primitives are installed. A governed inventory mapping each managed Pi to an approved address, account, host key, and credential is still needed before remote execution or transfer can be validated safely.

## Existing local services

The following services were found active and enabled and were left in place:

- BCA front-desk scanner bridge
- Node-RED
- Mosquitto MQTT
- Nginx
- PostgreSQL
- OpenSSH
- Tailscale
- x11vnc and XRDP
- Samba
- CUPS and Avahi

No existing Blast workload was removed, replaced, restarted, or reconfigured.

## Tracked local source and configuration

The repository now includes:

- All 12 BCA database migrations
- Five BCA administration, scanner, backup, and status scripts
- The BCA scanner and Node-RED systemd units
- Node-RED dependency manifests, settings, and static logo
- The existing BCA backup schedule as documentation/configuration

The live Node-RED flow was not imported because it contains an email token and personal account references. Credential stores, user/runtime metadata, databases, backups, logs, MQTT credentials, sudoers files, Tailscale state, private keys, and generated Aptly data were also excluded.

## Security observations and remaining work

No security setting was changed during this bootstrap. Existing issues remain:

- UFW is disabled.
- Mosquitto accepts anonymous connections on all interfaces.
- x11vnc uses `-nopw`.
- The live Node-RED flow contains an email token and stale Raspberry Pi paths and commands.
- Node-RED HTTP authentication is not clearly configured.
- Node-RED has passwordless sudo access to scanner controls and broad `systemctl` power operations; this policy requires least-privilege review.

Before a site agent is implemented, the central architecture must define the authenticated cross-tailnet transport, bounded action schema, target identity and host-key lifecycle, artifact verification, service account, credential storage, replay/idempotency rules, result reporting, and audit handoff. Central Operations data, portal authorization, release authority, and fleet private keys must remain on the central control plane.
