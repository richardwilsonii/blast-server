# Blast Site Node

Originally bootstrapped August 30, 2026; site-agent implementation updated September 8, 2026.

## Architectural role

`blast-server` is the Lost Games / It's a Blast site executor/storage node. `trapped-server` remains the authority for authorization, governed target scope, Operations data, managed releases/artifact selection, portal behavior and global history.

The site node executes only closed-list requests already resolved by central. It does not host a Trapped portal, Rundeck, Operations replica, release catalogue or independent configuration authority.

## Tailnet state

The Trapped tailnet is the canonical destination. The earlier permanent-separate-tailnet bootstrap assumption was superseded by the active `WO-2026-08-30-merge-lost-into-trapped-tailnet.md` migration.

`blast-server` and `blast-pc` are already on the Trapped tailnet. `ax15`, `blast-imac`, `pt1` and `pt1player` remain in that separate migration track. The site-agent boundary is retained because Lost/Blast work and backups execute locally through `blast-server`, not because a second tailnet is required. No subnet route, exit-node route, IP forwarding or LAN bridge is used.

## Site runtime

Live runtime root:

```text
/home/blasty/trapped-site/
  backups/
  bin/
  cache/
  logs/
  manifests/
  queue/
  results/
  state/
```

Runtime payloads, backup data and SSH credentials remain outside Git. The tracked implementation is `site-agent/site_agent.py`; the RPIMon executor also uses the tracked pure helper `site-agent/trapped-rpimon7-flow`.

Result/replay records are bounded to 30 days and at most 1,000 JSON results. Cached managed artifacts are addressed by SHA-256.

## Central-to-site authentication

Central uses a dedicated Ed25519 automation identity, separate from the normal `blasty` maintenance login and separate from any Pi-management key. The authorized-key entry on `blast-server` is forced to the fixed site-agent executable and disables normal shell/forwarding use. The central endpoint pins the Blast host key under strict host-key checking.

No central Trapped fleet private key, Operations credential, release catalogue or portal credential is copied to this server.

On September 8, 2026, the protected `lost-blast` endpoint was installed on `trapped-server` and the central site-status protocol reported `AVAILABLE` with agent version `1.0.0`.

## Site-local Pi trust

Blast owns a separate site-local Pi management key plus a strict site-local `known_hosts`. A centrally resolved Lost/Blast target carries its governed current LAN address, but the site agent will not trust an unknown host key or widen target scope.

There are currently no governed Lost/Blast Pis registered in central Operations, so the Pi `known_hosts` store intentionally has zero enrolled device entries. When a real Lost/Blast Pi is identified/onboarded, verify that Pi's host key and authorize the Blast site-local public key for that device. Do not pre-trust LAN neighbors.

## Implemented site actions

The fixed agent currently implements:

- site status and connection checks;
- Lost/Blast LAN discovery;
- light/detailed inventory collection using the exact central collector payload;
- local full-Pi backup;
- Node-RED flow backup, change inspection, send and restore;
- legacy package deployment from the exact central package payload;
- managed software deployment for all five current catalogue components: RPIMon, Pi inventory, Pi backup watcher, Node-RED audit config and GoldenBullseye PMPhone/Sherpa;
- one-time next-local-03:00 scheduled reboot.

File-bearing requests are size/SHA-256 bound. Managed software uses the exact artifact selected centrally. Components needing Debian packages receive the checksum-recorded exact dependency closure from central; the Pi does not need access to the Trapped internal APT service.

`repair_ssh_access` and `transfer_image` remain protocol-defined explicit refusals until a bounded Blast-side executor is operationally needed. They never fall back to direct central execution.

## Node-RED safety

The site agent resolves the target's actual active Node-RED flow from runtime/configuration evidence rather than source filename. Before a send overwrites an existing active flow, Blast captures the current active flow and matching credentials locally. Cross-device send replaces only the flow; it does not replace target credentials. Central receives the small Node-RED safety material/metadata required by the governed recovery workflow.

## Pi backup policy

Blast keeps 14 completed local full-Pi backup generations per governed device, oldest first, under the site runtime backup root. Automatic multi-gigabyte full-Pi replication back to `trapped-server` is intentionally disabled during SETUP. Central golden images/software/configuration plus centrally mirrored Node-RED safety material provide the off-site recovery layer currently required.

## Existing Blast workloads

The host continues to run its existing BCA, Node-RED, Mosquitto, Nginx, PostgreSQL, SSH, Tailscale, x11vnc/XRDP, Samba, CUPS and Avahi workloads. Phase 3 did not replace those services with Trapped equivalents.

The initial server review recorded pre-existing security issues including disabled UFW, anonymous Mosquitto, x11vnc `-nopw`, unclear Node-RED HTTP authentication and broad Node-RED sudo capability. Those remain separate Blast hardening work; they are not site-agent prerequisites and no secret values belong in Git.

## Remaining work

1. Enroll verified Pi host keys and the Blast site-local public key as real Lost/Blast Pis become governed targets.
2. Continue the separate active tailnet migration work order for the remaining Lost devices; do not mix that migration with normal site-agent execution.
3. Add optional SSH-repair/image-transfer executors only if those workflows become useful enough to justify them.
4. Add telemetry buffering only if site operation demonstrates a need.
