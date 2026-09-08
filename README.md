# Blast Server

This repository owns the safe local source, configuration and operational documentation for the Lost Games / It's a Blast server.

`blast-server` is the active **Lost/Blast site execution and storage node** for the Trapped! Server platform. It is not a second Trapped control plane: central authorization, Operations identity/assignment, release selection, deployment history, portal behavior and architecture remain authoritative in `richardwilsonii/trapped-infrastructure`.

## Repository contents

- `bca/migrations/` — versioned BCA SQLite schema and seed migrations
- `bca/scripts/` — BCA backup, administration, status and ACR122U scanner utilities
- `config/systemd/` — safe custom service definitions used by the host
- `config/cron/` — documented local scheduled jobs
- `config/packages/` — prerequisite package manifests
- `node-red/` — dependency manifest, settings and static assets; live flows/credentials are excluded
- `site-agent/` — fixed bounded Trapped site-agent plus the pure RPIMon flow helper it uses locally
- `docs/site-node-bootstrap.md` — current site-node implementation/readiness record
- `docs/work-orders/WO-2026-08-30-merge-lost-into-trapped-tailnet.md` — separate active tailnet-consolidation track
- `SERVER_REVIEW.md` — initial server audit

## Trapped site runtime

The live site runtime is `/home/blasty/trapped-site`. It holds local backups, the SHA-256 artifact cache, result/replay records, state and logs outside Git. The site agent is invoked through a restricted SSH key whose forced command is the fixed agent executable; that automation identity cannot obtain a normal shell.
On September 8, 2026, the matching protected endpoint was enrolled on `trapped-server`; the central site-status path reports `blast-server` as `AVAILABLE` with agent version `1.0.0`.

The Trapped tailnet is now canonical. `blast-server` and `blast-pc` have already migrated; the remaining Lost devices are handled one at a time by the active migration work order. Site-local execution still routes through `blast-server` even when a Pi is on the same tailnet.

## Secrets

Never commit Node-RED flows or credential stores directly from `~/.node-red`, SSH private keys, Tailscale state, databases, backups, password hashes, MQTT credentials, environment files or generated Aptly content. The current live Node-RED flow requires sanitization before any future tracked export.

See `docs/site-node-bootstrap.md` for the site-agent contract, local backup policy, Pi trust model and remaining work.
