# Work Order — Merge Lost/Blast Devices into the Trapped Tailnet

## Status

READY

## Goal

Consolidate the small Lost/Blast Tailscale tailnet into the existing Trapped tailnet without disrupting the ~120-device Trapped network or losing management access to Lost/Blast machines during migration.

The **Trapped tailnet is the permanent/canonical tailnet**. Do not move the Trapped fleet.

This decision supersedes the earlier temporary architectural requirement in `WO-2026-08-30-blast-site-node-bootstrap.md` to preserve separate Lost/Blast and Trapped tailnets. The earlier bootstrap document remains a valid historical record of the state at that time.

## Known current state

### Trapped tailnet

- Existing production tailnet with approximately 120 devices.
- `trappedliveescaperoom@gmail.com` remains the tailnet Owner.
- Do not disturb or re-enroll the existing Trapped fleet.

### Lost/Blast tailnet

Known machines:

- `ax15`
- `blast-imac`
- `blast-pc`
- `blast-server`
- `pt1`
- `pt1player`

`lostgamesllc@gmail.com` has already been invited to the Trapped tailnet and made an **Admin**.

`blast-pc` has already successfully added the Trapped tailnet as another Tailscale account/tailnet and can switch between Lost and Trapped.

### Important incident already encountered

While `blast-pc` was active on Trapped and `blast-server` was still active only on Lost, Tailscale-based SSH from `blast-pc` to `blast-server` stopped working as expected because the two machines were on different active tailnets.

After switching `blast-pc` back to Lost, SSH access to `blast-server` was restored.

Then, while connected to `blast-server` over its **Lost Tailscale connection**, `sudo tailscale login` was run. That immediately changed/restarted the active Tailscale authentication path and dropped the SSH session.

**Do not repeat this.** Never change a host's active Tailscale identity while the only management path to that host depends on the Tailscale identity being changed.

The most recently documented LAN state for `blast-server` is:

- LAN address: `192.168.1.23/24`
- LAN subnet: `192.168.1.0/24`
- management account: `blasty`

Treat that IP as previously observed until verified. It has now been successfully used for recovery as described below.

### Verified recovery state — August 30, 2026

A working non-`blast-server`-Tailscale recovery path has now been established:

```text
blast-pc
  -> Lost tailnet
  -> blast-imac (Lost Tailscale IP 100.68.120.123)
  -> Lost local LAN
  -> blast-server at 192.168.1.23
```

From `blast-imac`, `ssh blasty@192.168.1.23` succeeded and an interactive shell on `blast-server` is available. This LAN hop remains usable even though `blast-server` itself is currently logged out of Tailscale.

Current `blast-server` Tailscale state observed from that recovered shell:

```text
tailscale status
=> Logged out.
```

The failed/aborted login attempt produced a browser authentication URL. **Do not commit, copy into documentation, or treat that URL as durable state.** If authentication is still pending, Work may use the current live URL only through the user's active session/browser; otherwise generate a fresh supported login flow from the protected LAN SSH session.

`tailscale switch --list` without sudo returned `Access denied: profiles access denied`; use `sudo tailscale switch --list` for read-only profile inspection. Do not run another identity-changing command until the current profile/account state is understood and the LAN recovery shell is confirmed active.

## Safety rules

1. Migrate **one device at a time**.
2. Do not delete any device from the old Lost tailnet until that device is confirmed working on Trapped.
3. Before changing Tailscale identity on any remote machine, establish a management path that does **not** depend on the Tailscale session being changed: local LAN SSH, physical console, or another verified recovery path.
4. For `blast-server`, preserve the now-verified path `blast-pc -> Lost tailnet -> blast-imac -> LAN 192.168.1.23 -> blast-server` until Trapped-side access is independently verified.
5. Verify the current LAN IP before future reliance if the SSH session is lost or DHCP state changes.
6. Do not change hostnames, application configuration, Node-RED, MQTT, PostgreSQL, BCA, scanner services, firewall policy, or unrelated networking as part of this migration.
7. Do not enable subnet routing, exit-node routing, or broad LAN advertisement merely to make the migration easier.
8. Do not modify the existing ~120-device Trapped fleet.
9. Do not commit Tailscale auth keys, node keys, login URLs, state files, credentials, or other secrets to Git.
10. If an unexpected condition appears, preserve access and stop rather than improvising a destructive recovery.

## Phase 1 — Verify account/tailnet state

Using the current Tailscale admin console and current official Tailscale documentation where needed:

1. Confirm `lostgamesllc@gmail.com` is an Admin on the Trapped tailnet.
2. Confirm `blast-pc` is visible and connected on Trapped when that account/tailnet is selected.
3. Confirm the six Lost/Blast device names above are still represented on the old Lost tailnet.
4. Record any discrepancy before changing devices.

Do not remove old-tailnet entries yet.

## Phase 2 — Recover and migrate `blast-server` first

`blast-server` is the priority because it is the site node and because the previous Tailscale-login attempt dropped remote access.

### Preserve the verified non-Tailscale recovery path

The recovery path is already proven and currently reaches an interactive shell on `blast-server`:

```text
blast-pc -> Lost Tailscale -> blast-imac -> 192.168.1.23 LAN SSH -> blast-server
```

Before making another Tailscale identity change:

1. Keep `blast-pc` active on the Lost tailnet.
2. Keep the SSH session through `blast-imac` to `blast-server` open.
3. Run read-only inspection first, including `sudo tailscale switch --list`, `tailscale status`, IP addresses, routes, hostname, and relevant service state.
4. Determine whether a usable prior profile exists or whether `blast-server` must authenticate fresh into Trapped.
5. Do not close the LAN SSH session merely because a browser authentication step succeeds.

### Add/switch `blast-server` to Trapped

Use the current supported Tailscale CLI workflow for this installed version. The goal is to add/select the Trapped tailnet under `lostgamesllc@gmail.com` while connected through the verified LAN SSH path so a Tailscale restart or identity switch cannot strand the session.

Do not assume an old CLI sequence if current Tailscale behavior differs; verify the supported command flow before executing it.

If browser authentication is required, Work may operate the Tailscale browser/admin portion, but terminal commands must be executed only through the verified `blast-server` LAN SSH shell unless Work actually has direct terminal access. If Work cannot execute the command itself, give the user exactly one command at a time and wait for the output before continuing.

After `blast-server` is active on Trapped:

1. Confirm it appears online in the Trapped Machines list with the expected hostname.
2. Record its new/current Trapped Tailscale IP and DNS name if applicable.
3. Switch `blast-pc` to Trapped.
4. Verify Tailscale reachability from `blast-pc` to `blast-server`.
5. Verify SSH from `blast-pc` to `blast-server` over the Trapped tailnet.
6. Verify critical Blast services remain running and reachable as before.
7. If Trapped connectivity fails, recover over the preserved `blast-imac` LAN path and restore a known-good state before doing anything else.

Do not remove the old Lost `blast-server` machine entry until all checks pass.

## Phase 3 — Migrate the remaining Lost/Blast devices

Migrate one at a time:

1. `blast-pc` — already has Trapped added; verify final active state and connectivity.
2. `ax15`
3. `blast-imac`
4. `pt1`
5. `pt1player`

For every device:

- establish or identify a recovery path first;
- add/select the Trapped tailnet;
- verify the device appears online in Trapped;
- verify expected peer/application connectivity;
- verify no unrelated service was broken;
- only then proceed to the next device.

Use GUI account switching where appropriate on Windows/macOS and the supported CLI workflow on Linux. Do not perform a bulk migration until the individual method is proven.

## Phase 4 — Cleanup old Lost tailnet

Only after **all six devices** are confirmed working on Trapped:

1. Confirm normal Lost/Blast operations are working.
2. Confirm `blast-pc` can manage `blast-server` over Trapped.
3. Confirm no Lost/Blast workflow still depends on the old Lost tailnet addresses.
4. Remove stale machine registrations from the old Lost tailnet only after verification.
5. Do not attempt to transfer ownership of or destructively remove the Gmail-created Lost tailnet merely for cosmetic cleanup. It can remain empty/dormant if Tailscale does not provide a safe reason to remove it.

## Networking boundary after consolidation

Joining the same Tailscale tailnet does **not** authorize broad cross-site access by itself. Preserve least-privilege access using Tailscale ACLs/tags as needed.

Do not advertise the Lost LAN (`192.168.1.0/24`) as a subnet route as part of this work. Other locations may use overlapping RFC1918 subnets, and subnet routing is a separate design decision.

The desired outcome is individual Lost/Blast devices joining the Trapped tailnet, not merging physical LAN broadcast domains.

## Documentation updates after successful migration

After the migration succeeds:

- update `docs/site-node-bootstrap.md` with a clearly dated note that the Lost/Blast site was later consolidated into the Trapped tailnet;
- update this work order to `COMPLETE` with actual device-by-device results;
- update any affected central architecture documentation in `richardwilsonii/trapped-infrastructure` so it no longer claims the separate Lost/Blast tailnet is an architectural requirement;
- preserve the original bootstrap statements as historical observations rather than silently rewriting what was true during bootstrap.

## Acceptance criteria

Complete only when:

1. All six Lost/Blast devices are visible and online on the Trapped tailnet.
2. The existing Trapped fleet remains unaffected.
3. `lostgamesllc@gmail.com` retains appropriate Trapped administrative access.
4. `blast-pc` can reach and SSH to `blast-server` over Trapped.
5. Critical `blast-server` local services remain functional.
6. No device was stranded without a recovery path during migration.
7. No subnet route, exit node, broad bridge, or unrelated network/security change was introduced as a shortcut.
8. Old Lost machine entries are removed only after their Trapped replacements are verified.
9. Repo documentation reflects the completed migration without exposing secrets.
10. Any central architecture documentation that required separate tailnets is updated to reflect the approved consolidation decision.

## Final report

Return a concise report containing:

- each migrated device and result;
- old and new tailnet state;
- `blast-server` LAN recovery path used;
- Trapped-side SSH/connectivity verification;
- any Tailscale ACL/tag changes made;
- any old Lost entries removed;
- any remaining blockers or follow-up work;
- repo files/central architecture files updated.
