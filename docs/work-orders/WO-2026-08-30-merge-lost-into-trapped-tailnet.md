# Work Order — Merge Lost/Blast Devices into the Trapped Tailnet

## Status

IN PROGRESS

## Goal

Consolidate the small Lost/Blast Tailscale tailnet into the existing Trapped tailnet without disrupting the existing Trapped fleet or losing management access during migration.

The **Trapped tailnet is the permanent/canonical tailnet**. Do not move or re-enroll the existing Trapped fleet.

This decision supersedes the earlier temporary bootstrap requirement to preserve separate Lost/Blast and Trapped tailnets. Historical bootstrap documentation should remain historically accurate.

## Accounts

- Trapped tailnet Owner: `trappedliveescaperoom@gmail.com`
- `lostgamesllc@gmail.com` has already been added to the Trapped tailnet as an **Admin**.

## Lost/Blast devices in scope

- `ax15`
- `blast-imac`
- `blast-pc`
- `blast-server`
- `pt1`
- `pt1player`

## Completed progress — August 30, 2026

### `blast-pc`

- Trapped tailnet was added successfully as a second selectable Tailscale profile.
- `blast-pc` can switch between the old Lost tailnet and Trapped.
- After `blast-server` was migrated, `blast-pc` was switched to Trapped and direct Trapped-side connectivity to `blast-server` was verified.

### `blast-server`

A first migration attempt was made while SSH was connected over the old Lost Tailscale path. Running `sudo tailscale login` immediately dropped that SSH session. This established the rule that no remote host may have its active Tailscale identity changed unless a non-Tailscale recovery path is already verified.

Recovery was completed using:

```text
blast-pc
  -> old Lost tailnet
  -> blast-imac (100.68.120.123)
  -> Lost local LAN
  -> blast-server (192.168.1.23)
```

From `blast-imac`, LAN SSH to `blasty@192.168.1.23` succeeded. That session was kept open while Tailscale was re-authenticated.

Before migration, `sudo tailscale switch --list` showed only the old Lost profile:

```text
ID    Tailnet                 Account
3e7b  lostgamesllc@gmail.com  lostgamesllc@gmail.com
```

A fresh `sudo tailscale login` was then performed safely from the LAN SSH session. Authentication to the Trapped tailnet succeeded.

After authentication, `sudo tailscale switch --list` showed both profiles and Trapped active:

```text
ID    Tailnet                          Account
3e7b  lostgamesllc@gmail.com           lostgamesllc@gmail.com
7b1b  trappedliveescaperoom@gmail.com  trappedliveescaperoom@gmail.com*
```

Verified Trapped Tailscale IP for `blast-server`:

```text
100.71.88.22
```

`blast-pc` was then switched to the Trapped tailnet and direct connectivity/SSH to `blast-server` over Trapped was confirmed by the Owner.

**Result: `blast-server` and `blast-pc` are now successfully reunited on the Trapped tailnet.**

Do not remove the old Lost registrations yet; cleanup waits until all six devices are confirmed working on Trapped.

## Safety rules for remaining devices

1. Migrate **one device at a time**.
2. Before changing Tailscale identity on any remote machine, establish a recovery path that does not depend on that Tailscale session.
3. Do not remove old Lost machine entries until the replacement on Trapped is verified.
4. Do not modify the existing Trapped fleet.
5. Do not enable subnet routing, exit-node routing, or advertise the Lost LAN as a shortcut.
6. Do not change application services, hostnames, firewall policy, Node-RED, MQTT, PostgreSQL, BCA, scanner services, or unrelated networking.
7. Do not commit Tailscale keys, state, login URLs, credentials, or other secrets.
8. If anything unexpected occurs, preserve the working recovery path and stop rather than improvising.

## Remaining migration order

Continue one device at a time:

1. `ax15`
2. `blast-imac`
3. `pt1`
4. `pt1player`

For each device:

- identify/verify a recovery path first;
- add/select the Trapped tailnet;
- verify it appears online on Trapped;
- verify expected peer/application connectivity;
- confirm no unrelated service was broken;
- retain the old Lost registration until verification is complete;
- only then continue to the next device.

Use GUI account switching where appropriate and the supported Tailscale CLI workflow on Linux.

## Final cleanup

Only after all six devices are confirmed working on Trapped:

1. Confirm normal Lost/Blast operations are working.
2. Confirm `blast-pc` can still manage `blast-server` over Trapped.
3. Confirm no workflow depends on old Lost Tailscale addresses.
4. Remove stale Lost machine registrations.
5. The old Gmail-created Lost tailnet may remain empty/dormant; do not destructively remove it merely for cosmetic cleanup.
6. Update `docs/site-node-bootstrap.md` with a dated post-bootstrap note explaining the later tailnet consolidation.
7. Update affected central architecture documentation in `richardwilsonii/trapped-infrastructure` so separate Lost/Blast and Trapped tailnets are no longer documented as a requirement.
8. Mark this work order `COMPLETE` and record actual device-by-device results.

## Acceptance criteria

Complete only when:

1. All six Lost/Blast devices are visible and online on the Trapped tailnet.
2. The existing Trapped fleet remains unaffected.
3. `lostgamesllc@gmail.com` retains Trapped administrative access.
4. `blast-pc` can reach and SSH to `blast-server` over Trapped.
5. Critical `blast-server` services remain functional.
6. No device was stranded without a recovery path.
7. No subnet route, exit node, broad bridge, or unrelated network/security change was introduced.
8. Old Lost entries are removed only after their Trapped replacements are verified.
9. Repo documentation reflects the completed migration without exposing secrets.
10. Central architecture documentation reflects the approved consolidated-tailnet design.

## Final report

Return a concise report containing:

- each migrated device and result;
- old and new tailnet state;
- recovery path used where applicable;
- Trapped-side connectivity/SSH verification;
- any Tailscale ACL/tag changes;
- old Lost entries removed;
- remaining blockers/follow-up work;
- repo and central-architecture files updated.
