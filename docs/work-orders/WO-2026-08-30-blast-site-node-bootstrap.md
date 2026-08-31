# Work Order — Blast Site Node Bootstrap

## Status

READY

## Goal

Continue preparing `blast-server` to become the Lost Games / It's a Blast site execution/storage node for the Trapped! Server platform **without duplicating the Trapped central control plane**.

The Trapped architecture authority is `richardwilsonii/trapped-infrastructure`, especially:

- `docs/roadmap.md`
- `WORKING-RULES.md`
- `docs/systems/multi-location.md`
- `docs/systems/software-distribution.md`
- `docs/systems/backups-recovery.md`
- `docs/systems/networking-mqtt.md`

The Blast host/repo authority is this repository, especially `SERVER_REVIEW.md` and the live host state.

## Architectural boundary

`blast-server` is a **site executor/storage node**, not another `trapped-server`.

Do not install or create independent copies of:

- Rundeck or the Trapped portal;
- the authoritative Trapped Operations PostgreSQL database;
- Trapped portal identities/authorization authority;
- the managed-software release catalogue/authority;
- global audit/deployment-history authority;
- Cloudflare portal infrastructure;
- a second authoritative package/release-management system.

Existing Blast/Lost applications already on the machine (BCA, Node-RED, MQTT, PostgreSQL, scanner, etc.) are separate local workloads and should not be removed merely because Trapped has analogous services.

## Current known Blast state

`SERVER_REVIEW.md` records an existing server with BCA utilities/database migrations, Node-RED, Mosquitto, PostgreSQL, Tailscale, scanner service, x11vnc, backup scheduling and related local configuration.

Important known issues from that review include:

- UFW disabled;
- x11vnc configured with `-nopw`;
- Mosquitto anonymous access;
- live Node-RED email token in the current flow;
- stale Raspberry Pi `/home/pi` paths/hardware commands in Node-RED;
- privileged Node-RED sudo commands requiring review;
- Node-RED HTTP authentication not clearly documented.

Do not expose or commit secrets while reviewing any of these.

## Phase 1 — Inventory software and prerequisites

Inspect the live `blast-server` first. Do not reinstall packages that are already present and suitable.

Determine and record whether these site-node prerequisites are installed and usable:

- `tailscale`
- `openssh-server`
- `openssh-client`
- `rsync`
- `python3`
- `bash`
- `iproute2`
- `iputils-ping`
- `coreutils`
- `sudo`
- `git`

Install only missing required packages.

Do **not** add `nmap` or `arp-scan` merely for Trapped discovery. The current Trapped discovery implementation uses `ping`, `ip route`, `ip addr`, and `ip neigh`.

Also inventory, but do not reinstall or replace solely for Trapped purposes, the existing local services/packages documented in `SERVER_REVIEW.md`.

## Phase 2 — Establish site-node filesystem layout

Create a minimal local layout suitable for later Trapped site execution. Use a Blast-specific root so it cannot be confused with central Trapped authority. Preferred layout unless live constraints justify a better equivalent:

```text
/srv/trapped-site/
  backups/
  cache/
  queue/
  results/
  manifests/
  state/
  logs/
```

Choose ownership/permissions deliberately. Do not place reusable secrets in these directories unless a later authenticated site-agent design explicitly requires a protected credential path.

Document the final paths and permissions.

## Phase 3 — SSH readiness

Prepare the host for the future execution model, without inventing the not-yet-designed cross-site protocol.

Required outcomes:

1. `blast-server` has working SSH server/client tooling.
2. Identify the intended local management account and current SSH configuration.
3. Inventory current SSH reachability to local Pis without changing production Pis unless explicitly authorized.
4. Do not copy Trapped fleet private keys, Operations credentials, or central server secrets into the repository.
5. Do not create a broad trust relationship or disable strict host-key checking as a shortcut.

If a secure central `trapped-server -> blast-server` path cannot yet be configured because the cross-tailnet transport/authentication design is not implemented, record that as remaining work rather than inventing a second authority or bridging entire tailnets.

## Phase 4 — Tailscale boundary

Confirm the host is joined to the **Lost/Blast tailnet**, not the Trapped tailnet.

Do not:

- move all Blast/Lost Pis into the Trapped tailnet;
- expose the full Lost/Blast LAN to the Trapped tailnet;
- make `blast-server` an unrestricted subnet bridge merely to make management convenient.

The future design must allow central management to reach this one governed site node while preserving the separate Lost/Blast tailnet boundary.

Record the current state and any blocker, but do not invent the final cross-tailnet implementation in this work order.

## Phase 5 — Local LAN execution prerequisites

Confirm the server can perform the same basic site-local primitives the Trapped repo will need to move here later:

- determine the default LAN interface;
- determine the local IPv4 subnet;
- run `ip neigh`;
- run bounded `ping` probes;
- make outbound SSH connections to local managed devices where current credentials already allow it;
- perform local file transfer with `rsync`/SSH.

Do not run an unbounded network scan or mutate production Pis solely to prove readiness.

## Phase 6 — Repository housekeeping

Bring the `blast-server` repository into a usable state without committing secrets.

At minimum:

- retain `SERVER_REVIEW.md` as historical/current audit material or move it under `docs/audits/` with a clear reference;
- add a defensive `.gitignore` covering the exclusions already identified in `SERVER_REVIEW.md`;
- add/update `README.md` describing that this repo owns the Blast/Lost local server and that Trapped central authority remains in `richardwilsonii/trapped-infrastructure`;
- document the installed site-node prerequisites and `/srv/trapped-site` layout;
- import only safe, deliberate configuration/source files from the existing server where appropriate;
- do not commit live Node-RED flows until sanitized;
- do not commit Node-RED credentials/user/runtime files, private keys, Tailscale state, database dumps, password hashes, MQTT credentials, `.env` files, backup payloads, or generated Aptly data.

Do not duplicate Trapped architecture documentation into this repository. Link/reference the central repo for central-platform behavior.

## Phase 7 — Do not copy the current Trapped executors unchanged

The current Trapped implementations are still central-server coupled. In particular, current backup and managed-deployment code reads the local Operations database/credentials and assumes central authority paths.

Therefore do **not** simply install current copies of `trapped-pi-backup`, `trapped-managed-deployment`, `trapped-rpimon-target-deploy`, the portal runtime, or related central scripts on `blast-server` and then copy Operations credentials/database state to make them work.

The future implementation must split central planning/authority from site-local execution:

```text
trapped-server
  resolves authorization, location, targets, exact software/artifact,
  compatibility and requested action
        |
        v
blast-server site runtime
  receives bounded resolved action
  executes only against Lost/Blast local targets
  returns per-target results
```

This work order is for host/bootstrap readiness only. Do not design a competing site protocol ad hoc unless the implementation is explicitly added to the Trapped architecture first.

## Acceptance criteria

This work order is complete when:

1. Required site-node prerequisite software has been inventoried and only missing required packages installed.
2. No Trapped central-control-plane service has been duplicated on `blast-server`.
3. `/srv/trapped-site/` (or a documented equivalent) exists with deliberate ownership/permissions.
4. SSH, Tailscale, LAN-interface/subnet, `ip neigh`, ping and rsync readiness are documented from the live host.
5. The Lost/Blast tailnet boundary is preserved.
6. The Blast repo contains safe bootstrap/operations documentation and defensive exclusions without secrets.
7. Existing Blast workloads remain functional and are not replaced with Trapped equivalents merely for consistency.
8. Any work that requires the not-yet-built site dispatcher/cross-tailnet protocol is clearly listed as remaining work rather than solved by duplicating the Operations DB, portal, release authority or credentials.
9. Commit all completed repo changes to `richardwilsonii/blast-server` with a concise completion summary.

## Final report

Return a concise report containing:

- packages already present;
- packages installed;
- relevant services found;
- site-node filesystem created;
- SSH/Tailscale/LAN readiness;
- security issues corrected, if any;
- files added/changed in the repo;
- blockers/remaining work for the later Trapped site-agent integration.
