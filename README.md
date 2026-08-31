# Blast Server

This repository owns the configuration, operational documentation, and safe local source for the Lost Games / It's a Blast server.

`blast-server` is a **site executor and storage node** for future Trapped integrations. It is not a second Trapped control plane. Central authorization, release selection, deployment history, portal behavior, and architecture remain authoritative in [`richardwilsonii/trapped-infrastructure`](https://github.com/richardwilsonii/trapped-infrastructure).

## Repository contents

- `bca/migrations/` — versioned BCA SQLite schema and seed migrations
- `bca/scripts/` — BCA backup, administration, status, and ACR122U scanner utilities
- `config/systemd/` — safe custom service definitions currently used by the host
- `config/cron/` — documented local scheduled jobs
- `config/packages/` — prerequisite package manifests
- `node-red/` — dependency manifest, settings, and static assets; live flows and credentials are intentionally excluded
- `docs/site-node-bootstrap.md` — live site-node readiness and operations record
- `SERVER_REVIEW.md` — initial server audit

## Site runtime boundary

The prepared runtime root is `/home/blasty/trapped-site`, a documented non-root equivalent of the preferred `/srv/trapped-site`. It contains empty `backups`, `cache`, `queue`, `results`, `manifests`, `state`, and `logs` directories. Runtime payloads and secrets do not belong in Git.

No Rundeck, Trapped portal, Operations database, release catalogue, Cloudflare portal infrastructure, or central Trapped executors are installed by this repository.

## Secrets

Never commit Node-RED flows or credential stores directly from `~/.node-red`, SSH keys, Tailscale state, databases, backups, password hashes, MQTT credentials, environment files, or generated Aptly content. The current live Node-RED flow requires sanitization before a future export can be tracked.

See [docs/site-node-bootstrap.md](docs/site-node-bootstrap.md) for current readiness, security observations, and remaining integration work.
