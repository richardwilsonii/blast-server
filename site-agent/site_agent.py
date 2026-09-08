#!/usr/bin/env python3
"""Bounded Lost/Blast site executor for the Trapped central control plane."""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import ipaddress
import json
import os
import pathlib
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import uuid

SCHEMA_VERSION = 1
AGENT_VERSION = "1.0.0"
SITE = "lost-blast"
SITE_NODE = "blast-server"
ROOT = pathlib.Path(os.environ.get("TRAPPED_SITE_ROOT", "/home/blasty/trapped-site"))
STATE = ROOT / "state"
CACHE = ROOT / "cache"
RESULTS = ROOT / "results"
BACKUPS = ROOT / "backups"
LOGS = ROOT / "logs"
SSH_STATE = STATE / "pi-ssh.json"
MAX_HEADER = 131072
MAX_RESULT_DATA = 16777216
MAX_PAYLOAD = 2_147_483_648
RESULT_RETENTION_DAYS = 30
RESULT_RETENTION_MAX = 1000
NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,62}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PAYLOAD_NAME = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
ACTIONS = {
    "discover_unknown_devices", "check_device_connections", "collect_device_inventory",
    "backup_pi", "backup_nodered_flow", "restore_nodered_flow", "send_nodered_flow",
    "find_nodered_changes", "deploy_managed_software", "deploy_legacy_package",
    "collect_detailed_configuration", "repair_ssh_access", "schedule_device_reboot",
    "transfer_image", "site_status",
}
TARGETED = ACTIONS - {"discover_unknown_devices", "site_status"}
PAYLOAD_ACTIONS = {
    "deploy_managed_software": {"artifact", "config", "dependencies"}, "deploy_legacy_package": {"artifact"},
    "transfer_image": {"artifact"}, "send_nodered_flow": {"flow"},
    "restore_nodered_flow": {"flow", "credentials"},
    "collect_device_inventory": {"collector"},
    "collect_detailed_configuration": {"collector"},
}
OUTCOMES = {"SUCCESS", "ALREADY_CURRENT", "NO_CHANGES", "OFFLINE", "BLOCKED",
            "INCOMPATIBLE", "FAILED", "ROLLED_BACK", "NOT_ATTEMPTED"}

class AgentError(Exception):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def result_path(request_id: str) -> pathlib.Path:
    return RESULTS / f"{request_id}.json"


def prune_results() -> None:
    """Bound replay evidence by age and count without following links."""
    try:
        RESULTS.mkdir(parents=True, exist_ok=True)
        files = [p for p in RESULTS.iterdir()
                 if p.is_file() and not p.is_symlink() and p.suffix == ".json"]
        cutoff = dt.datetime.now(dt.timezone.utc).timestamp() - RESULT_RETENTION_DAYS * 86400
        for path in files:
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
            except FileNotFoundError:
                pass
        files = sorted((p for p in RESULTS.iterdir()
                        if p.is_file() and not p.is_symlink() and p.suffix == ".json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for path in files[RESULT_RETENTION_MAX:]:
            try: path.unlink()
            except FileNotFoundError: pass
    except OSError:
        # Retention housekeeping must not make an otherwise executable request fail.
        pass


def safe_write_json(path: pathlib.Path, value: dict, mode: int = 0o640) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temp, mode)
        os.replace(temp, path)
    finally:
        try: os.unlink(temp)
        except FileNotFoundError: pass


def bounded_data(value):
    if value is None:
        return None
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > MAX_RESULT_DATA:
        raise AgentError("action data exceeds the protocol bound")
    return value


def read_request() -> tuple[dict, dict[str, bytes]]:
    header = sys.stdin.buffer.readline(MAX_HEADER + 1)
    if not header or len(header) > MAX_HEADER or not header.endswith(b"\n"):
        raise AgentError("request header is missing or too large")
    try:
        request = json.loads(header.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentError("request header is not valid JSON") from exc
    validate_request(request)
    payloads: dict[str, bytes] = {}
    for item in request.get("payloads") or []:
        name, size, digest = item["name"], item["size_bytes"], item["sha256"]
        payload = sys.stdin.buffer.read(size)
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise AgentError(f"payload {name!r} did not match its descriptor")
        payloads[name] = payload
    if sys.stdin.buffer.read(1):
        raise AgentError("request contains bytes after the declared payloads")
    return request, payloads


def validate_request(request: object) -> None:
    if not isinstance(request, dict) or request.get("schema_version") != SCHEMA_VERSION:
        raise AgentError("unsupported site-agent protocol version")
    try: request["request_id"] = str(uuid.UUID(str(request.get("request_id"))))
    except (ValueError, TypeError) as exc: raise AgentError("request_id is not a UUID") from exc
    if request.get("site") != SITE or request.get("site_node") != SITE_NODE:
        raise AgentError("request is for a different site or node")
    action = str(request.get("action") or "")
    if action not in ACTIONS: raise AgentError("request names an unsupported action")
    targets = request.get("targets") or []
    if not isinstance(targets, list): raise AgentError("targets must be a list")
    if action in TARGETED and not targets: raise AgentError("target action has no targets")
    if action not in TARGETED and targets: raise AgentError("site-wide action cannot carry targets")
    seen = set()
    for target in targets:
        if not isinstance(target, dict): raise AgentError("target is not a document")
        name = str(target.get("canonical_name") or "").lower()
        if not NAME.fullmatch(name) or name in seen: raise AgentError("target identity is invalid or duplicated")
        try: target["device_id"] = str(uuid.UUID(str(target.get("device_id"))))
        except (ValueError, TypeError) as exc: raise AgentError(f"target {name} has no valid device id") from exc
        target["canonical_name"] = name
        if target.get("lan_ip"):
            try:
                address = ipaddress.ip_address(str(target["lan_ip"]))
                if address.version != 4 or not address.is_private: raise ValueError
            except ValueError as exc: raise AgentError(f"target {name} has no private IPv4 LAN address") from exc
        seen.add(name)
    descriptors = request.get("payloads") or []
    if not isinstance(descriptors, list): raise AgentError("payload descriptors must be a list")
    allowed = PAYLOAD_ACTIONS.get(action, set())
    payload_seen = set()
    for item in descriptors:
        if not isinstance(item, dict): raise AgentError("payload descriptor is not a document")
        name = str(item.get("name") or "")
        digest = str(item.get("sha256") or "").lower()
        size = item.get("size_bytes")
        if name not in allowed or not PAYLOAD_NAME.fullmatch(name) or name in payload_seen:
            raise AgentError(f"unsupported payload {name!r} for {action}")
        if not SHA256.fullmatch(digest) or not isinstance(size, int) or size < 0 or size > MAX_PAYLOAD:
            raise AgentError(f"invalid payload descriptor for {name!r}")
        payload_seen.add(name)


def base_result(request: dict, state: str, targets: list[dict] | None = None,
                reason: str = "", data=None, started: str | None = None) -> dict:
    return {"schema_version": SCHEMA_VERSION, "request_id": request["request_id"],
            "site": SITE, "site_node": SITE_NODE, "action": request["action"],
            "result": state, "targets": targets or [], "reason": reason[:1000],
            "started_at": started or now(), "completed_at": now(),
            "agent_version": AGENT_VERSION, "data": bounded_data(data)}


def target_result(target: dict, outcome: str, reason: str = "", data=None) -> dict:
    if outcome not in OUTCOMES: raise AgentError(f"invalid target outcome {outcome}")
    row = {"canonical_name": target["canonical_name"], "outcome": outcome, "reason": reason[:500]}
    if data is not None: row["data"] = bounded_data(data)
    return row


def overall(rows: list[dict]) -> str:
    ok = sum(row["outcome"] in {"SUCCESS", "ALREADY_CURRENT", "NO_CHANGES"} for row in rows)
    if ok == len(rows): return "SUCCESS"
    if ok: return "PARTIAL_SUCCESS"
    return "FAILED"


def load_ssh_config() -> dict:
    if SSH_STATE.is_symlink() or not SSH_STATE.is_file():
        raise AgentError(f"site-local Pi SSH trust is not configured at {SSH_STATE}")
    try: config = json.loads(SSH_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise AgentError("site-local Pi SSH config is unreadable") from exc
    user = str(config.get("user") or "")
    identity = pathlib.Path(str(config.get("identity_file") or ""))
    known_hosts = pathlib.Path(str(config.get("known_hosts") or ""))
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", user): raise AgentError("site-local Pi SSH user is invalid")
    for path in (identity, known_hosts):
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            raise AgentError("site-local Pi SSH identity/known-hosts file is not installed")
    return {"user": user, "identity": str(identity), "known_hosts": str(known_hosts)}


def ssh_command(target: dict, remote_command: str) -> list[str]:
    config = load_ssh_config()
    address = str(target.get("lan_ip") or "")
    if not address: raise AgentError(f"{target['canonical_name']} has no centrally resolved LAN address")
    return ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
            "-o", f"UserKnownHostsFile={config['known_hosts']}", "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes", "-o", "ConnectTimeout=8",
            "-o", f"HostKeyAlias={target['canonical_name']}", "-i", config["identity"],
            f"{config['user']}@{address}", "--", remote_command]


def ssh(target: dict, command: str, *, stdin: bytes | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(ssh_command(target, command), input=stdin, capture_output=True,
                          check=False, timeout=timeout)


def transport_reason(run: subprocess.CompletedProcess) -> tuple[str, str]:
    detail = run.stderr.decode("utf-8", "replace").strip().splitlines()
    text = detail[-1][:400] if detail else "the device did not answer"
    low = text.lower()
    if "host key" in low or "known_hosts" in low or "permission denied" in low:
        return "BLOCKED", text
    if "timed out" in low or "no route" in low or "unreachable" in low or "refused" in low:
        return "OFFLINE", text
    return "FAILED", text


def cache_artifact(request: dict, payloads: dict[str, bytes]) -> pathlib.Path | None:
    artifact = request.get("artifact")
    if not artifact: return None
    digest = str(artifact["sha256"])
    root = CACHE / "sha256"
    root.mkdir(parents=True, exist_ok=True)
    path = root / digest
    payload = payloads.get("artifact")
    if payload is not None:
        if hashlib.sha256(payload).hexdigest() != digest: raise AgentError("artifact payload does not match central identity")
        if not path.exists():
            temp = root / f".{digest}.{os.getpid()}"
            temp.write_bytes(payload); os.chmod(temp, 0o640); os.replace(temp, path)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise AgentError("exact artifact is not available in the site cache")
    return path


def site_status(request: dict, payloads: dict[str, bytes]) -> dict:
    configured = SSH_STATE.is_file() and not SSH_STATE.is_symlink()
    known_count = 0
    if configured:
        try:
            cfg=json.loads(SSH_STATE.read_text(encoding="utf-8"))
            known_hosts=pathlib.Path(str(cfg.get("known_hosts") or ""))
            if known_hosts.is_file() and not known_hosts.is_symlink():
                known_count=sum(1 for line in known_hosts.read_text(encoding="utf-8").splitlines()
                                if line.strip() and not line.lstrip().startswith("#"))
        except (OSError,json.JSONDecodeError):
            configured=False
    data = {"runtime_root": str(ROOT), "pi_ssh_configured": configured,
            "pi_known_hosts_entries": known_count, "pi_backup_retention": 14,
            "cached_artifacts": len(list((CACHE / "sha256").glob("*"))) if (CACHE / "sha256").is_dir() else 0}
    return base_result(request, "SUCCESS", data=data)


def check_connections(request: dict, payloads: dict[str, bytes]) -> dict:
    rows=[]
    for target in request["targets"]:
        try: run=ssh(target, "true", timeout=15)
        except (AgentError, OSError, subprocess.TimeoutExpired) as exc:
            rows.append(target_result(target, "BLOCKED" if isinstance(exc, AgentError) else "OFFLINE", str(exc))); continue
        if run.returncode == 0: rows.append(target_result(target, "SUCCESS", "strict site-local SSH answered"))
        else:
            outcome, reason=transport_reason(run); rows.append(target_result(target,outcome,reason))
    return base_result(request, overall(rows), rows)

def collect_inventory(request: dict, payloads: dict[str, bytes]) -> dict:
    collector = payloads.get("collector")
    if collector is None:
        raise AgentError("inventory collection requires the exact central collector payload")
    params = request.get("parameters") or {}
    mode = str(params.get("mode") or "detailed")
    collection_reason = str(params.get("reason") or "site-agent")
    if mode not in {"light", "detailed"} or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}", collection_reason):
        raise AgentError("inventory parameters are invalid")
    rows=[]; data={}
    command=f"python3 - --mode {shlex.quote(mode)} --reason {shlex.quote(collection_reason)}"
    if bool(params.get("force")):
        command += " --force"
    for target in request["targets"]:
        try:
            run=ssh(target, command, stdin=collector, timeout=180)
        except (AgentError, OSError, subprocess.TimeoutExpired) as exc:
            rows.append(target_result(target,"BLOCKED" if isinstance(exc,AgentError) else "OFFLINE",str(exc))); continue
        if run.returncode not in {0,2} or not run.stdout.strip():
            outcome, reason_text=transport_reason(run); rows.append(target_result(target,outcome,reason_text)); continue
        try: manifest=json.loads(run.stdout.decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError):
            rows.append(target_result(target,"FAILED","inventory collector response was not JSON")); continue
        if (not isinstance(manifest,dict) or manifest.get("schema_version") != 1
                or (manifest.get("collector") or {}).get("name") != "trapped-inventory"):
            rows.append(target_result(target,"FAILED","inventory collector response used an unsupported schema")); continue
        data[target["canonical_name"]]=manifest
        outcome="SUCCESS" if str(manifest.get("result") or "failed").lower() in {"success","partial"} else "FAILED"
        rows.append(target_result(target,outcome,"exact central inventory collector completed"))
    return base_result(request, overall(rows), rows, data=data)


PI_BACKUP_KEEP = 14


def prune_pi_backups(root: pathlib.Path) -> None:
    archives=sorted(p for p in root.glob("*.tar.gz") if p.is_file() and not p.is_symlink())
    for archive in archives[:-PI_BACKUP_KEEP]:
        meta=archive.with_name(archive.name.removesuffix(".tar.gz") + ".json")
        archive.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)


def backup_pi(request: dict, payloads: dict[str, bytes]) -> dict:
    rows=[]; data={}
    excludes=("./proc","./sys","./dev","./run","./tmp","./mnt","./media","./lost+found","./swapfile")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    for target in request["targets"]:
        name=target["canonical_name"]; root=BACKUPS/"pi"/name; root.mkdir(parents=True,exist_ok=True)
        partial=root/f"{stamp}.tar.gz.partial"; final=root/f"{stamp}.tar.gz"
        command="sudo -n tar --one-file-system " + " ".join(f"--exclude={x}" for x in excludes) + " -C / -czf - ."
        try:
            proc=subprocess.Popen(ssh_command(target,command),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            assert proc.stdout is not None
            with partial.open("wb") as handle: shutil.copyfileobj(proc.stdout,handle,1024*1024)
            stderr=(proc.stderr.read() if proc.stderr else b"").decode("utf-8","replace")
            code=proc.wait(timeout=900)
        except (AgentError,OSError,subprocess.TimeoutExpired) as exc:
            partial.unlink(missing_ok=True); rows.append(target_result(target,"BLOCKED" if isinstance(exc,AgentError) else "OFFLINE",str(exc))); continue
        if code:
            partial.unlink(missing_ok=True); fake=subprocess.CompletedProcess([],code,b"",stderr.encode()); outcome,reason=transport_reason(fake); rows.append(target_result(target,outcome,reason)); continue
        os.replace(partial,final); digest=hashlib.sha256(final.read_bytes()).hexdigest()
        meta={"backup_id":stamp,"sha256":digest,"bytes":final.stat().st_size,"storage":"site-local-primary"}
        safe_write_json(root/f"{stamp}.json",meta); prune_pi_backups(root)
        data[name]=meta; rows.append(target_result(target,"SUCCESS","site-local Pi backup captured"))
    return base_result(request,overall(rows),rows,data=data)

FLOW_RESOLVER = r'''set -eu
python3 - <<'PYF'
import glob,json,os,re,subprocess

def read(cmd):
  try:return subprocess.check_output(cmd,shell=True,text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
  except Exception:return ''
user=read("systemctl show nodered.service -p User --value 2>/dev/null") or ('pi' if os.path.isdir('/home/pi/.node-red') else '')
home=read("getent passwd %s | cut -d: -f6"%user) if user else ''
userdir=(home+'/.node-red') if home else ''
proc=read("ps -eo args | grep -E '[n]ode-red|[r]ed.js' | head -1")
if '--userDir ' in proc:
  m=re.search(r'--userDir(?:=|\\s+)([^ ]+)',proc); userdir=m.group(1).strip("'\\\"") if m else userdir
flow=''
settings=os.path.join(userdir,'settings.js') if userdir else ''
if settings and os.path.isfile(settings):
  text=open(settings,errors='ignore').read()
  m=re.search(r'flowFile\\s*:\\s*[\\\"\\\']([^\\\"\\\']+)',text)
  if m: flow=m.group(1)
if flow and not flow.startswith('/'): flow=os.path.join(userdir,flow)
if not flow and userdir:
  candidates=[p for p in glob.glob(os.path.join(userdir,'flows*.json')) if not p.endswith('_cred.json') and '_cred.' not in p]
  if len(candidates)==1: flow=candidates[0]
if not flow:
  print(json.dumps({'path':'','reason':'active_flow_unresolved'})); raise SystemExit
base=os.path.basename(flow)
cred=os.path.join(os.path.dirname(flow),base[:-5]+'_cred.json') if base.endswith('.json') else flow+'_cred.json'
print(json.dumps({'path':flow,'basename':base,'credential_path':cred,'credential_basename':os.path.basename(cred),
                  'user_dir':userdir,'flow_exists':os.path.isfile(flow),'credential_exists':os.path.isfile(cred),
                  'service_active':read('systemctl is-active nodered.service 2>/dev/null')=='active','runtime_user':user}))
PYF'''


def resolve_flow(target: dict) -> dict:
    run=ssh(target,"sh -s",stdin=FLOW_RESOLVER.encode(),timeout=30)
    if run.returncode:
        outcome,reason=transport_reason(run); raise AgentError(f"{outcome}: {reason}")
    try: value=json.loads(run.stdout.decode())
    except json.JSONDecodeError as exc: raise AgentError("active-flow resolver returned invalid JSON") from exc
    if not value.get("path"): raise AgentError(str(value.get("reason") or "active flow unresolved"))
    return value


def read_remote(target: dict,path: str) -> bytes:
    run=ssh(target,"sudo -n cat -- "+shlex.quote(path),timeout=60)
    if run.returncode: raise AgentError(transport_reason(run)[1])
    return run.stdout


def write_flow_snapshot(target: dict,resolution: dict) -> dict:
    flow=read_remote(target,str(resolution["path"])); creds=None
    if resolution.get("credential_exists"): creds=read_remote(target,str(resolution["credential_path"]))
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    root=BACKUPS/"nodered"/target["canonical_name"]/stamp; root.mkdir(parents=True,exist_ok=False)
    (root/resolution["basename"]).write_bytes(flow); os.chmod(root/resolution["basename"],0o640)
    if creds is not None:
        (root/resolution["credential_basename"]).write_bytes(creds); os.chmod(root/resolution["credential_basename"],0o600)
    meta={"backup_id":stamp,"active_flow_file":resolution["basename"],"active_flow_path":resolution["path"],
          "user_dir":resolution["user_dir"],"flow_sha256":hashlib.sha256(flow).hexdigest(),
          "credential_file":resolution["credential_basename"],"credential_path":resolution["credential_path"],
          "credential_present":creds is not None,"storage":"site-local-primary"}
    safe_write_json(root/"manifest.json",meta); return {**meta,"snapshot_dir":str(root)}


def export_flow_snapshot(meta: dict) -> dict:
    root=pathlib.Path(str(meta["snapshot_dir"]))
    flow=(root/str(meta["active_flow_file"])).read_bytes()
    creds=None
    if meta.get("credential_present"):
        creds=(root/str(meta["credential_file"])).read_bytes()
    return {**meta,
            "flow_base64":base64.b64encode(flow).decode("ascii"),
            "credentials_base64":base64.b64encode(creds).decode("ascii") if creds is not None else None}


def backup_nodered(request: dict,payloads: dict[str,bytes]) -> dict:
    rows=[]; data={}
    for target in request["targets"]:
        try: resolution=resolve_flow(target); meta=write_flow_snapshot(target,resolution)
        except (AgentError,OSError) as exc: rows.append(target_result(target,"BLOCKED",str(exc))); continue
        data[target["canonical_name"]]=export_flow_snapshot(meta)
        rows.append(target_result(target,"SUCCESS","active flow and matching credentials captured locally and returned for central mirroring"))
    return base_result(request,overall(rows),rows,data=data)


def validate_node_array(payload: bytes) -> None:
    try: value=json.loads(payload.decode())
    except (UnicodeDecodeError,json.JSONDecodeError) as exc: raise AgentError("flow payload is not valid JSON") from exc
    if not isinstance(value,list) or not value or not all(isinstance(x,dict) and x.get('id') and x.get('type') for x in value):
        raise AgentError("flow payload is not a Node-RED node array")


def remote_stat(target: dict,path: str) -> tuple[str,str]:
    quoted=shlex.quote(path); run=ssh(target,f"sudo -n stat -c '%U:%G %a' -- {quoted}")
    if run.returncode: raise AgentError(transport_reason(run)[1])
    parts=run.stdout.decode().strip().split(); return parts[0],parts[1]


def install_remote_file(target: dict,path: str,payload: bytes,owner: str,mode: str) -> None:
    staged=path+f".trapped-site-{uuid.uuid4().hex[:8]}"; q=shlex.quote
    run=ssh(target,f"sudo -n tee {q(staged)} >/dev/null",stdin=payload,timeout=120)
    if run.returncode: raise AgentError(transport_reason(run)[1])
    expected=hashlib.sha256(payload).hexdigest()
    run=ssh(target,f"sudo -n sha256sum {q(staged)} | awk '{{print $1}}'")
    if run.returncode or run.stdout.decode().strip()!=expected:
        ssh(target,f"sudo -n rm -f {q(staged)}"); raise AgentError("staged file checksum did not match")
    run=ssh(target,f"sudo -n chown {shlex.quote(owner)} {q(staged)} && sudo -n chmod {shlex.quote(mode)} {q(staged)} && sudo -n mv {q(staged)} {q(path)}")
    if run.returncode: raise AgentError(transport_reason(run)[1])


def send_nodered(request: dict,payloads: dict[str,bytes]) -> dict:
    flow=payloads.get("flow")
    if flow is None: raise AgentError("send_nodered_flow requires a flow payload")
    validate_node_array(flow); rows=[]; data={}
    for target in request["targets"]:
        try:
            resolution=resolve_flow(target)
            if not resolution.get("flow_exists"): raise AgentError("resolved active flow does not exist")
            backup=write_flow_snapshot(target,resolution)
            exported=export_flow_snapshot(backup)
            owner,mode=remote_stat(target,resolution["path"])
            install_remote_file(target,resolution["path"],flow,owner,mode)
            result_data={"active_flow_path":resolution["path"],
                         "installed_sha256":hashlib.sha256(flow).hexdigest(),
                         "pre_change_backup":exported,"credentials_preserved":True}
            if resolution.get("service_active"):
                restart=ssh(target,"sudo -n systemctl restart nodered.service",timeout=90)
                if restart.returncode:
                    prior=(pathlib.Path(backup["snapshot_dir"])/backup["active_flow_file"]).read_bytes()
                    install_remote_file(target,resolution["path"],prior,owner,mode)
                    recovered=ssh(target,"sudo -n systemctl restart nodered.service",timeout=90)
                    result_data["node_red"]="rollback-restored" if recovered.returncode == 0 else "rollback-failed"
                    data[target["canonical_name"]]=result_data
                    rows.append(target_result(target,"ROLLED_BACK" if recovered.returncode == 0 else "FAILED",
                                              "Node-RED restart failed; prior flow restored" if recovered.returncode == 0 else "Node-RED restart failed and rollback restart also failed"))
                    continue
                result_data["node_red"]="restarted"
            else:
                result_data["node_red"]="not-running"
            data[target["canonical_name"]]=result_data
            rows.append(target_result(target,"SUCCESS","active flow replaced; target credentials preserved"))
        except (AgentError,OSError) as exc: rows.append(target_result(target,"FAILED",str(exc)))
    return base_result(request,overall(rows),rows,data=data)


CREDENTIAL_STATE_SCRIPT = r'''import hashlib,json,pathlib,re,sys
root=pathlib.Path(sys.argv[1]); label=b"trapped-nodered-credential-secret-v1\x00"
rx=re.compile(r"^[^/*]*\\bcredentialSecret\\s*:\\s*(?P<value>\\\"[^\\\"]*\\\"|'[^']*'|false|true)",re.M)
def done(cls,fp=None,source=None):
 print(json.dumps({'class':cls,'fingerprint':fp,'source':source},separators=(',',':'))); raise SystemExit
try: text=(root/'settings.js').read_text(errors='ignore')
except OSError: text=''
active='\\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('//'))
m=rx.search(active)
if m:
 raw=m.group('value')
 if raw=='false': done('disabled',None,'settings.js')
 if raw not in {'true','""',"''"}:
  secret=raw[1:-1]; done('explicit',hashlib.sha256(label+secret.encode()).hexdigest(),'settings.js')
for name in ('.config.runtime.json','.config.json'):
 try: value=json.loads((root/name).read_text())
 except (OSError,json.JSONDecodeError): continue
 secret=value.get('_credentialSecret') if isinstance(value,dict) else None
 if isinstance(secret,str) and secret: done('generated',hashlib.sha256(label+secret.encode()).hexdigest(),name)
done('unknown')'''


def target_credential_state(target: dict, resolution: dict) -> dict:
    run=ssh(target,"sudo -n python3 - "+shlex.quote(str(resolution["user_dir"])),
            stdin=CREDENTIAL_STATE_SCRIPT.encode(),timeout=30)
    if run.returncode: raise AgentError(transport_reason(run)[1])
    try: state=json.loads(run.stdout.decode())
    except json.JSONDecodeError as exc: raise AgentError("credential-key probe returned invalid JSON") from exc
    return state if isinstance(state,dict) else {"class":"unknown","fingerprint":None}


def restore_nodered(request: dict,payloads: dict[str,bytes]) -> dict:
    params=request.get("parameters") or {}; preview=bool(params.get("preview"))
    flow=payloads.get("flow"); creds=payloads.get("credentials")
    if not preview and flow is None: raise AgentError("restore_nodered_flow requires a flow payload")
    if flow is not None: validate_node_array(flow)
    rows=[]; data={}
    for target in request["targets"]:
        try:
            resolution=resolve_flow(target); key_state=target_credential_state(target,resolution)
            if preview:
                data[target["canonical_name"]]={"active_flow_path":resolution["path"],
                    "user_dir":resolution["user_dir"],"credential_path":resolution["credential_path"],
                    "credential_exists":bool(resolution.get("credential_exists")),"target_key":key_state}
                rows.append(target_result(target,"SUCCESS","restore target facts resolved")); continue
            if creds is not None:
                source_class=str(params.get("source_key_class") or "unknown")
                source_fp=str(params.get("source_key_fingerprint") or "") or None
                target_class=str(key_state.get("class") or "unknown"); target_fp=key_state.get("fingerprint")
                compatible=(source_class==target_class=="disabled") or (
                    source_class in {"explicit","generated"} and target_class in {"explicit","generated"}
                    and source_fp and source_fp==target_fp)
                if not compatible: raise AgentError("credential restore blocked because source and target credential keys do not match")
            owner,mode=remote_stat(target,resolution["path"]); install_remote_file(target,resolution["path"],flow,owner,mode)
            if creds is not None:
                if resolution.get("credential_exists"): cowner,cmode=remote_stat(target,resolution["credential_path"])
                else: cowner,cmode=owner,"600"
                install_remote_file(target,resolution["credential_path"],creds,cowner,cmode)
            if resolution.get("service_active"):
                restart=ssh(target,"sudo -n systemctl restart nodered.service",timeout=90)
                if restart.returncode: raise AgentError("Node-RED did not restart after restore")
            data[target["canonical_name"]]={"active_flow_path":resolution["path"],
                "installed_sha256":hashlib.sha256(flow).hexdigest(),"credentials_restored":creds is not None}
            rows.append(target_result(target,"SUCCESS","same-device Node-RED restore applied"))
        except (AgentError,OSError) as exc: rows.append(target_result(target,"FAILED",str(exc)))
    return base_result(request,overall(rows),rows,data=data)


def nodered_changes(request: dict,payloads: dict[str,bytes]) -> dict:
    rows=[]; data={}
    for target in request["targets"]:
        try:
            r=resolve_flow(target); q=shlex.quote
            cmd=f"stat -c '%Y %s' {q(r['path'])}; stat -c '%Y %s' {q(r['credential_path'])} 2>/dev/null || true"
            run=ssh(target,cmd); lines=run.stdout.decode().splitlines()
            data[target["canonical_name"]]={"active_flow_path":r["path"],"flow_stat":lines[0] if lines else "","credential_stat":lines[1] if len(lines)>1 else ""}
            rows.append(target_result(target,"SUCCESS","Node-RED file state observed"))
        except (AgentError,OSError) as exc: rows.append(target_result(target,"FAILED",str(exc)))
    return base_result(request,overall(rows),rows,data=data)


def legacy_package(request: dict,payloads: dict[str,bytes]) -> dict:
    artifact=cache_artifact(request,payloads); assert artifact is not None
    meta=request["artifact"]; name=str(meta.get("artifact_name") or meta.get("component") or "package")
    params=request.get("parameters") or {}; expected_suite=str(params.get("suite") or ""); expected_arch=str(params.get("architecture") or "")
    rows=[]
    for target in request["targets"]:
        try:
            probe=ssh(target,". /etc/os-release; printf '%s %s' \"${VERSION_CODENAME:-}\" \"$(dpkg --print-architecture)\"")
            if probe.returncode: outcome,reason=transport_reason(probe); rows.append(target_result(target,outcome,reason)); continue
            parts=probe.stdout.decode().split(); suite=parts[0] if parts else ""; arch=parts[1] if len(parts)>1 else ""
            if expected_suite and suite!=expected_suite or expected_arch and arch!=expected_arch:
                rows.append(target_result(target,"INCOMPATIBLE",f"target is {suite}/{arch}, package requires {expected_suite}/{expected_arch}")); continue
            remote=f"/tmp/trapped-site-{request['request_id']}.deb"; payload=artifact.read_bytes(); q=shlex.quote
            stage=ssh(target,f"sudo -n tee {q(remote)} >/dev/null",stdin=payload,timeout=180)
            if stage.returncode: raise AgentError(transport_reason(stage)[1])
            verify=ssh(target,f"echo '{meta['sha256']}  {q(remote)}' | sudo -n sha256sum -c -")
            if verify.returncode: raise AgentError("target package checksum did not match")
            install=ssh(target,f"sudo -n dpkg -i {q(remote)}",timeout=300); ssh(target,f"sudo -n rm -f {q(remote)}")
            if install.returncode: raise AgentError(transport_reason(install)[1])
            rows.append(target_result(target,"SUCCESS",f"installed {name}"))
        except (AgentError,OSError,subprocess.TimeoutExpired) as exc: rows.append(target_result(target,"FAILED",str(exc)))
    return base_result(request,overall(rows),rows)


def safe_extract(archive: pathlib.Path,destination: pathlib.Path) -> None:
    with tarfile.open(archive,"r:gz") as tf:
        for member in tf.getmembers():
            target=(destination/member.name).resolve()
            if destination.resolve() not in target.parents and target!=destination.resolve(): raise AgentError("artifact contains an unsafe path")
        tf.extractall(destination,filter="data")


def managed_package_root(artifact: pathlib.Path, request: dict, work: pathlib.Path) -> tuple[pathlib.Path, dict]:
    root = work / "artifact"
    root.mkdir(parents=True, exist_ok=True)
    safe_extract(artifact, root)
    manifests = [path for path in root.rglob("manifest.json") if path.is_file() and not path.is_symlink()]
    if len(manifests) != 1:
        raise AgentError("managed artifact does not contain one package manifest")
    package = manifests[0].parent
    try:
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentError("managed artifact manifest is unreadable") from exc
    meta = request.get("artifact") or {}
    component = str(manifest.get("component_key") or "")
    version = str(manifest.get("release_version") or manifest.get("version") or "")
    if component != str(meta.get("component") or "") or version != str(meta.get("version") or ""):
        raise AgentError("managed artifact manifest differs from the central release identity")
    if str(manifest.get("build_profile") or "") != str(meta.get("build_profile") or ""):
        raise AgentError("managed artifact build profile differs from the central release identity")
    if str(manifest.get("resource_profile") or "standard") != str(meta.get("resource_profile") or "standard"):
        raise AgentError("managed artifact resource profile differs from the central release identity")
    return package, manifest


def dependency_bundle(payload: bytes | None, request: dict, work: pathlib.Path) -> pathlib.Path | None:
    if payload is None:
        return None
    archive = work / "dependencies.tar.gz"
    archive.write_bytes(payload)
    root = work / "dependencies"
    root.mkdir()
    safe_extract(archive, root)
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentError("managed dependency bundle is unreadable") from exc
    params = request.get("parameters") or {}
    meta = request.get("artifact") or {}
    if (manifest.get("component"), manifest.get("version"), manifest.get("suite"), manifest.get("architecture")) != (
            meta.get("component"), meta.get("version"), params.get("suite"), params.get("architecture")):
        raise AgentError("managed dependency bundle identity differs from the target request")
    packages = manifest.get("packages") or []
    if not packages:
        raise AgentError("managed dependency bundle contains no packages")
    for item in packages:
        rel = str(item.get("path") or "")
        path = (root / rel).resolve()
        if root.resolve() not in path.parents or not path.is_file() or path.is_symlink():
            raise AgentError("managed dependency bundle contains an unsafe package path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != str(item.get("sha256") or ""):
            raise AgentError("managed dependency package checksum does not match its manifest")
    return archive


def stage_remote_archive(target: dict, archive: bytes, remote_root: str, name: str = "artifact.tar.gz") -> None:
    q = shlex.quote
    path = f"{remote_root}/{name}"
    run = ssh(target, f"set -eu; rm -rf -- {q(remote_root)}; install -d -m 0700 {q(remote_root)}; cat > {q(path)}",
              stdin=archive, timeout=300)
    if run.returncode:
        raise AgentError(transport_reason(run)[1])


def install_dependency_bundle(target: dict, bundle: bytes | None, request: dict) -> None:
    if bundle is None:
        return
    remote = f"/tmp/trapped-site-deps-{request['request_id']}"
    q = shlex.quote
    stage_remote_archive(target, bundle, remote, "dependencies.tar.gz")
    command = (f"set -eu; tar -xzf {q(remote + '/dependencies.tar.gz')} -C {q(remote)}; "
               f"files=$(find {q(remote + '/packages')} -maxdepth 1 -type f -name '*.deb' -print | sort); "
               "test -n \"$files\"; sudo -n dpkg -i $files || sudo -n dpkg -i $files")
    run = ssh(target, command, timeout=900)
    ssh(target, f"rm -rf -- {q(remote)}", timeout=30)
    if run.returncode:
        raise AgentError(transport_reason(run)[1])


def stage_component(target: dict, artifact: pathlib.Path, package_name: str, request: dict) -> tuple[str, str]:
    remote = f"/tmp/trapped-site-managed-{request['request_id']}"
    q = shlex.quote
    stage_remote_archive(target, artifact.read_bytes(), remote)
    run = ssh(target, f"set -eu; tar -xzf {q(remote + '/artifact.tar.gz')} -C {q(remote)}; test -d {q(remote + '/' + package_name)}", timeout=180)
    if run.returncode:
        raise AgentError(transport_reason(run)[1])
    return remote, remote + "/" + package_name


def install_inventory(target: dict, package: pathlib.Path) -> tuple[str, str]:
    candidates = [p for p in package.rglob("trapped-inventory") if p.is_file() and not p.is_symlink()]
    if len(candidates) != 1:
        raise AgentError("inventory artifact does not contain one collector payload")
    payload = candidates[0].read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    check = ssh(target, "sha256sum /usr/local/bin/trapped-inventory 2>/dev/null | awk '{print $1}' || true")
    if check.returncode == 0 and check.stdout.decode().strip() == digest:
        return "ALREADY_CURRENT", "exact inventory collector already installed"
    install_remote_file(target, "/usr/local/bin/trapped-inventory", payload, "root:root", "0755")
    return "SUCCESS", "exact managed inventory collector installed"


def install_audit(target: dict, artifact: pathlib.Path, package: pathlib.Path, request: dict) -> tuple[str, str]:
    remote, pkg = stage_component(target, artifact, package.name, request)
    q = shlex.quote
    try:
        run = ssh(target, f"sudo -n bash {q(pkg + '/install.sh')}", timeout=180)
        if run.returncode == 10:
            return "ALREADY_CURRENT", "Node-RED audit configuration already enabled"
        if run.returncode:
            raise AgentError(transport_reason(run)[1])
        verify = ssh(target, f"sudo -n bash {q(pkg + '/verify.sh')}", timeout=90)
        if verify.returncode:
            raise AgentError("Node-RED audit configuration verification failed")
        return "SUCCESS", "Node-RED audit configuration installed"
    finally:
        ssh(target, f"rm -rf -- {q(remote)}", timeout=30)


def install_backup_watch(target: dict, artifact: pathlib.Path, package: pathlib.Path,
                         config: bytes | None, dependencies: bytes | None, request: dict) -> tuple[str, str]:
    if config is None:
        raise AgentError("backup-watch deployment requires its central generated config")
    install_dependency_bundle(target, dependencies, request)
    remote, pkg = stage_component(target, artifact, package.name, request)
    q = shlex.quote
    cfg = remote + "/trapped-backup-watch.conf"
    run = ssh(target, f"cat > {q(cfg)}", stdin=config, timeout=60)
    if run.returncode:
        raise AgentError(transport_reason(run)[1])
    expected = hashlib.sha256(config).hexdigest()
    script = r'''set -eu
pkg="$1"; cfg="$2"; expected="$3"
install -d -o root -g root -m 0755 /var/lib/trapped-backup
install -o root -g root -m 0755 "$pkg/trapped-backup-watch" /usr/local/sbin/trapped-backup-watch
install -o root -g root -m 0644 "$pkg/trapped-backup-watch.service" /etc/systemd/system/trapped-backup-watch.service
install -o root -g root -m 0644 "$cfg" /etc/trapped-backup-watch.conf
if [ ! -e /var/lib/trapped-backup/change.marker ]; then cat /proc/sys/kernel/random/uuid >/var/lib/trapped-backup/change.marker; chmod 0644 /var/lib/trapped-backup/change.marker; fi
test "$(sha256sum /etc/trapped-backup-watch.conf | awk '{print $1}')" = "$expected"
systemctl daemon-reload
systemctl enable --now trapped-backup-watch.service >/dev/null
systemctl is-active --quiet trapped-backup-watch.service
'''
    try:
        run = ssh(target, "sudo -n bash -s -- " + q(pkg) + " " + q(cfg) + " " + q(expected), stdin=script.encode(), timeout=180)
        if run.returncode:
            raise AgentError(transport_reason(run)[1])
        return "SUCCESS", "Pi backup watcher installed from the exact artifact"
    finally:
        ssh(target, f"rm -rf -- {q(remote)}", timeout=30)


def install_pmphone(target: dict, artifact: pathlib.Path, package: pathlib.Path,
                    dependencies: bytes | None, request: dict) -> tuple[str, str]:
    if dependencies is None:
        raise AgentError("GoldenBullseye PMPhone deployment requires its exact package closure")
    install_dependency_bundle(target, dependencies, request)
    remote, pkg = stage_component(target, artifact, package.name, request)
    q = shlex.quote
    deployment = str((request.get("parameters") or {}).get("deployment_id") or request["request_id"])
    rollback = f"/var/lib/trapped/goldenbullseye-pmphone/deployment-rollback/{deployment}"
    capture = r'''set -eu
rb="$1"; install -d -m 0700 "$rb"; : >"$rb/paths"
for p in /home/pi/wakeword.py /home/pi/run_wakeword.sh /home/pi/sherpa-kws/keywords_raw.txt /home/pi/sherpa-kws/keywords.txt /home/pi/sherpa-kws/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01 /home/pi/.local/share/goldenbullseye-pmphone/python /var/lib/trapped/goldenbullseye-pmphone/status.json; do
 if [ -e "$p" ]; then printf '%s\n' "$p" >>"$rb/paths"; cp -a --parents "$p" "$rb"; fi
done
'''
    run = ssh(target, "sudo -n bash -s -- " + q(rollback), stdin=capture.encode(), timeout=120)
    if run.returncode:
        raise AgentError("could not capture PMPhone rollback state")
    install = r'''set -eu
pkg="$1"; model=/home/pi/sherpa-kws/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01
python_root=/home/pi/.local/share/goldenbullseye-pmphone/python
install -d -o pi -g pi -m 0755 /home/pi/sherpa-kws "$model" "$(dirname "$python_root")"
rm -rf -- "$python_root"; install -d -o pi -g pi -m 0755 "$python_root"
python3 -m zipfile -e "$pkg/sherpa_onnx-1.12.1-cp39-cp39-linux_armv7l.whl" "$python_root"
python3 -m zipfile -e "$pkg/pypinyin-0.55.0-py2.py3-none-any.whl" "$python_root"
chown -R pi:pi "$python_root"
install -o pi -g pi -m 0755 "$pkg/wakeword.py" /home/pi/wakeword.py
install -o pi -g pi -m 0755 "$pkg/run_wakeword.sh" /home/pi/run_wakeword.sh
install -o pi -g pi -m 0644 "$pkg/keywords_raw.txt" /home/pi/sherpa-kws/keywords_raw.txt
install -o pi -g pi -m 0644 "$pkg/keywords.txt" /home/pi/sherpa-kws/keywords.txt
install -o pi -g pi -m 0644 "$pkg/model-bpe.model" "$model/bpe.model"
install -o pi -g pi -m 0644 "$pkg/model-tokens.txt" "$model/tokens.txt"
install -o pi -g pi -m 0644 "$pkg/model-encoder.int8.onnx" "$model/encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx"
install -o pi -g pi -m 0644 "$pkg/model-decoder.int8.onnx" "$model/decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx"
install -o pi -g pi -m 0644 "$pkg/model-joiner.int8.onnx" "$model/joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx"
'''
    validate = r'''import pathlib
import numpy,pyaudio,sentencepiece,pypinyin,sherpa_onnx
assert sherpa_onnx.__version__ == "1.12.1"
assert pypinyin.__version__ == "0.55.0"
source=pathlib.Path('/home/pi/wakeword.py').read_text(); compile(source,'wakeword.py','exec')
assert 'picovoice' not in source.lower() and 'porcupine' not in source.lower()
launcher=pathlib.Path('/home/pi/run_wakeword.sh').read_text(); assert '--device 10' in launcher
base='/home/pi/sherpa-kws/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01'
k=sherpa_onnx.KeywordSpotter(tokens=f'{base}/tokens.txt',encoder=f'{base}/encoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx',decoder=f'{base}/decoder-epoch-12-avg-2-chunk-16-left-64.int8.onnx',joiner=f'{base}/joiner-epoch-12-avg-2-chunk-16-left-64.int8.onnx',keywords_file='/home/pi/sherpa-kws/keywords.txt',num_threads=1)
assert k.create_stream() is not None
a=pyaudio.PyAudio()
try: assert int(a.get_device_info_by_index(10).get('maxInputChannels') or 0)>0
finally: a.terminate()
print('VALID')
'''
    try:
        run = ssh(target, "sudo -n bash -s -- " + q(pkg), stdin=install.encode(), timeout=300)
        if run.returncode:
            raise AgentError(transport_reason(run)[1])
        run = ssh(target, "sudo -n -u pi env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/home/pi/.local/share/goldenbullseye-pmphone/python /usr/bin/python3 -",
                  stdin=validate.encode(), timeout=180)
        if run.returncode or run.stdout.decode().strip() != "VALID":
            raise AgentError("target-local Sherpa validation failed")
        status = json.dumps({"component_key": "goldenbullseye-pmphone", "release_version": (request.get("artifact") or {}).get("version"),
                             "artifact_sha256": (request.get("artifact") or {}).get("sha256"), "deployment_id": deployment}, sort_keys=True).encode() + b"\n"
        install_remote_file(target, "/var/lib/trapped/goldenbullseye-pmphone/status.json", status, "root:root", "0644")
        return "SUCCESS", "GoldenBullseye Sherpa wake-word component installed"
    except (AgentError, OSError, subprocess.TimeoutExpired):
        rollback_script = r'''set -eu
rb="$1"
for p in /home/pi/wakeword.py /home/pi/run_wakeword.sh /home/pi/sherpa-kws/keywords_raw.txt /home/pi/sherpa-kws/keywords.txt /home/pi/sherpa-kws/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01 /home/pi/.local/share/goldenbullseye-pmphone/python /var/lib/trapped/goldenbullseye-pmphone/status.json; do rm -rf -- "$p"; done
if [ -f "$rb/paths" ]; then while IFS= read -r p; do rel="${p#/}"; [ -e "$rb/$rel" ] && cp -a "$rb/$rel" "$p"; done <"$rb/paths"; fi
'''
        restored = ssh(target, "sudo -n bash -s -- " + q(rollback), stdin=rollback_script.encode(), timeout=180)
        if restored.returncode == 0:
            raise AgentError("PMPhone deployment failed; previous component files were restored")
        raise AgentError("PMPhone deployment failed and rollback did not complete")
    finally:
        ssh(target, f"rm -rf -- {q(remote)}", timeout=30)


def install_rpimon(target: dict, artifact: pathlib.Path, request: dict) -> tuple[str, str]:
    resolution = resolve_flow(target)
    if not resolution.get("flow_exists"):
        raise AgentError("resolved active Node-RED flow does not exist")
    before = read_remote(target, str(resolution["path"]))
    dependency = "present"
    user_dir = str(resolution["user_dir"])
    q = shlex.quote
    check = ssh(target, f"test -d {q(user_dir + '/node_modules/node-red-dashboard')}")
    if check.returncode:
        generation = {"legacy-core": "2", "current-core": "3"}.get(str((request.get("artifact") or {}).get("build_profile") or ""))
        if generation:
            owner = ssh(target, f"stat -c %U {q(user_dir)}").stdout.decode().strip()
            cmd = f"cd {q(user_dir)} && npm install --no-audit --save node-red-dashboard@{generation}"
            run = ssh(target, (f"sudo -n -u {q(owner)} -H sh -c {q(cmd)}" if owner else f"sh -c {q(cmd)}"), timeout=300)
            dependency = "installed" if run.returncode == 0 else "not_installed"
    tool = pathlib.Path(__file__).with_name("trapped-rpimon7-flow")
    if not tool.is_file() or tool.is_symlink():
        raise AgentError("Blast RPIMon merge helper is not installed")
    with tempfile.TemporaryDirectory(prefix="trapped-rpimon-site-") as td:
        root = pathlib.Path(td)
        flow = root / "flows.json"
        candidate = root / "candidate.json"
        flow.write_bytes(before)
        run = subprocess.run([str(tool), "merge", "--flows", str(flow), "--artifact", str(artifact),
                              "--output", str(candidate), "--execute"], text=True, capture_output=True, check=False)
        if run.returncode:
            raise AgentError("RPIMon managed-flow merge refused: " + (run.stderr.strip() or run.stdout.strip())[:400])
        payload = candidate.read_bytes()
    if payload == before and dependency != "installed":
        return "ALREADY_CURRENT", "exact RPIMon flow is already installed"
    backup = write_flow_snapshot(target, resolution)
    owner, mode = remote_stat(target, resolution["path"])
    install_remote_file(target, resolution["path"], payload, owner, mode)
    if resolution.get("service_active"):
        restart = ssh(target, "sudo -n systemctl restart nodered.service", timeout=90)
        if restart.returncode:
            install_remote_file(target, resolution["path"], before, owner, mode)
            recovered = ssh(target, "sudo -n systemctl restart nodered.service", timeout=90)
            if recovered.returncode == 0:
                return "ROLLED_BACK", "Node-RED restart failed; prior flow restored"
            raise AgentError("Node-RED restart failed and the prior flow could not be restored to service")
    return "SUCCESS", f"managed RPIMon flow installed; dashboard dependency {dependency}; rollback {backup['snapshot_dir']}"


def managed_software(request: dict, payloads: dict[str, bytes]) -> dict:
    artifact = cache_artifact(request, payloads)
    assert artifact is not None
    component = str((request.get("artifact") or {}).get("component") or "")
    rows = []
    with tempfile.TemporaryDirectory(prefix="trapped-site-managed-") as td:
        work = pathlib.Path(td)
        package, manifest = managed_package_root(artifact, request, work)
        needs_dependencies = isinstance(manifest.get("managed_package_dependencies"), dict)
        deps = payloads.get("dependencies")
        if needs_dependencies and deps is None:
            return base_result(request, "REFUSED", [target_result(t, "BLOCKED", "exact managed package dependency closure is not available") for t in request["targets"]],
                               reason="the artifact requires managed packages but central supplied no exact dependency closure")
        if deps is not None:
            dependency_bundle(deps, request, work)
        for target in request["targets"]:
            try:
                probe = ssh(target, ". /etc/os-release; printf '%s %s' \"${VERSION_CODENAME:-}\" \"$(dpkg --print-architecture 2>/dev/null || true)\"")
                if probe.returncode:
                    outcome, reason = transport_reason(probe)
                    rows.append(target_result(target, outcome, reason))
                    continue
                parts = probe.stdout.decode().split()
                suite = parts[0] if parts else ""
                arch = parts[1] if len(parts) > 1 else ""
                params = request.get("parameters") or {}
                if params.get("suite") not in {"", None, "unknown", suite} or params.get("architecture") not in {"", None, "unknown", arch}:
                    rows.append(target_result(target, "INCOMPATIBLE", f"target is {suite}/{arch}, central resolved {params.get('suite')}/{params.get('architecture')}"))
                    continue
                if component == "trapped-pi-inventory":
                    outcome, reason = install_inventory(target, package)
                elif component == "trapped-nodered-audit-config":
                    outcome, reason = install_audit(target, artifact, package, request)
                elif component == "trapped-pi-backup-watch":
                    outcome, reason = install_backup_watch(target, artifact, package, payloads.get("config"), deps, request)
                elif component == "goldenbullseye-pmphone":
                    outcome, reason = install_pmphone(target, artifact, package, deps, request)
                elif component == "rpimon":
                    outcome, reason = install_rpimon(target, artifact, request)
                else:
                    outcome, reason = "BLOCKED", f"site executor for managed component {component or 'unknown'} is not installed"
                rows.append(target_result(target, outcome, reason))
            except (AgentError, OSError, subprocess.TimeoutExpired, tarfile.TarError) as exc:
                text = str(exc)
                outcome = "ROLLED_BACK" if "previous component files were restored" in text else "FAILED"
                rows.append(target_result(target, outcome, text))
    return base_result(request, overall(rows), rows)

def discover(request: dict,payloads: dict[str,bytes]) -> dict:
    route=subprocess.run(["ip","-4","route","show","default"],text=True,capture_output=True,check=False)
    default=route.stdout.strip().splitlines()[0] if route.stdout.strip() else ""
    dev=""; parts=default.split()
    if "dev" in parts:
        try: dev=parts[parts.index("dev")+1]
        except IndexError: pass
    if not dev: return base_result(request,"FAILED",reason="site LAN interface could not be resolved")
    addr=subprocess.run(["ip","-4","-o","addr","show","dev",dev],text=True,capture_output=True,check=False)
    cidr=""; fields=addr.stdout.split()
    if "inet" in fields:
        try: cidr=fields[fields.index("inet")+1]
        except IndexError: pass
    if not cidr: return base_result(request,"FAILED",reason="site LAN IPv4 subnet could not be resolved")
    network=ipaddress.ip_interface(cidr).network
    if network.prefixlen < 22: return base_result(request,"REFUSED",reason=f"refusing discovery of unexpectedly broad subnet {network}")
    # Bounded ping sweep using installed primitives, then read the kernel neighbour table.
    hosts=list(network.hosts())[:1022]
    procs=[]
    for ip in hosts:
        if str(ip)==cidr.split('/')[0]: continue
        procs.append(subprocess.Popen(["ping","-c","1","-W","1",str(ip)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        if len(procs)>=64:
            for proc in procs: proc.wait(timeout=3)
            procs=[]
    for proc in procs: proc.wait(timeout=3)
    neigh=subprocess.run(["ip","neigh","show","dev",dev],text=True,capture_output=True,check=False)
    candidates=[]
    for line in neigh.stdout.splitlines():
        bits=line.split()
        if not bits: continue
        try: ip=str(ipaddress.ip_address(bits[0]))
        except ValueError: continue
        if ipaddress.ip_address(ip) not in network: continue
        mac=bits[bits.index("lladdr")+1].lower() if "lladdr" in bits and len(bits)>bits.index("lladdr")+1 else ""
        state=bits[-1] if bits else ""
        if not mac or state in {"FAILED","INCOMPLETE"}: continue
        ssh_reachable=False
        try:
            with socket.create_connection((ip,22),timeout=0.75): ssh_reachable=True
        except OSError: pass
        candidates.append({"lan_ip":ip,"mac":mac,"neighbor_state":state,
                           "ssh_reachable":ssh_reachable})
    return base_result(request,"SUCCESS",data={"interface":dev,"subnet":str(network),"candidates":candidates})



REBOOT_SCHEDULE = r'''set -eu
umask 022
service=/etc/systemd/system/trapped-scheduled-reboot.service
timer=/etc/systemd/system/trapped-scheduled-reboot.timer
systemctl_bin="$(command -v systemctl || true)"
case "$systemctl_bin" in /*) ;; *) echo 'systemctl is unavailable' >&2; exit 20 ;; esac
now_epoch="$(date +%s)"; today="$(date +%F)"; when_epoch="$(date -d "$today 03:00:00" +%s)"
if [ "$now_epoch" -ge "$when_epoch" ]; then when_epoch="$(date -d 'tomorrow 03:00:00' +%s)"; fi
when_calendar="$(date -d "@$when_epoch" '+%Y-%m-%d %H:%M:%S')"
when_iso="$(date -d "@$when_epoch" '+%Y-%m-%dT%H:%M:%S%:z')"
service_tmp="$(mktemp /etc/systemd/system/.trapped-scheduled-reboot.service.XXXXXX)"
timer_tmp="$(mktemp /etc/systemd/system/.trapped-scheduled-reboot.timer.XXXXXX)"
cleanup() { rm -f "$service_tmp" "$timer_tmp"; }; trap cleanup EXIT HUP INT TERM
cat >"$service_tmp" <<EOF
[Unit]
Description=Trapped one-time scheduled reboot
[Service]
Type=oneshot
ExecStart=$systemctl_bin reboot
EOF
cat >"$timer_tmp" <<EOF
[Unit]
Description=Trapped one-time reboot scheduled for $when_calendar
[Timer]
OnCalendar=$when_calendar
AccuracySec=1s
Persistent=false
Unit=trapped-scheduled-reboot.service
[Install]
WantedBy=timers.target
EOF
"$systemctl_bin" stop trapped-scheduled-reboot.timer >/dev/null 2>&1 || true
install -o root -g root -m 0644 "$service_tmp" "$service"
install -o root -g root -m 0644 "$timer_tmp" "$timer"
"$systemctl_bin" daemon-reload
"$systemctl_bin" enable --now trapped-scheduled-reboot.timer >/dev/null
printf '%s\t%s\n' 'TRAPPED_SCHEDULED_REBOOT' "$when_iso"
'''


def schedule_reboot(request: dict,payloads: dict[str,bytes]) -> dict:
    rows=[]; data={}
    for target in request["targets"]:
        try:
            run=ssh(target,"sudo -n /bin/sh -s",stdin=REBOOT_SCHEDULE.encode(),timeout=60)
            if run.returncode:
                outcome,reason=transport_reason(run); rows.append(target_result(target,outcome,reason)); continue
            marker=None
            for line in run.stdout.decode("utf-8","replace").splitlines():
                if line.startswith("TRAPPED_SCHEDULED_REBOOT\t"):
                    marker=line.split("\t",1)[1].strip(); break
            if not marker:
                rows.append(target_result(target,"FAILED","Pi returned success without the scheduled reboot time")); continue
            data[target["canonical_name"]]={"scheduled_for":marker}
            rows.append(target_result(target,"SUCCESS",f"reboot scheduled for {marker}"))
        except (AgentError,OSError,subprocess.TimeoutExpired) as exc:
            rows.append(target_result(target,"FAILED",str(exc)))
    return base_result(request,overall(rows),rows,data=data)


def unsupported_bounded(request: dict,payloads: dict[str,bytes]) -> dict:
    rows=[target_result(t,"BLOCKED",f"the {request['action']} Blast-side executor is not installed") for t in request["targets"]]
    return base_result(request,"REFUSED",rows,reason=f"{request['action']} is defined by the protocol but has no local executor yet")

HANDLERS={
    "site_status":site_status,"check_device_connections":check_connections,
    "collect_device_inventory":collect_inventory,"collect_detailed_configuration":collect_inventory,
    "backup_pi":backup_pi,"backup_nodered_flow":backup_nodered,"send_nodered_flow":send_nodered,
    "restore_nodered_flow":restore_nodered,"find_nodered_changes":nodered_changes,
    "deploy_legacy_package":legacy_package,"deploy_managed_software":managed_software,
    "discover_unknown_devices":discover,"repair_ssh_access":unsupported_bounded,
    "schedule_device_reboot":schedule_reboot,"transfer_image":unsupported_bounded,
}


def main() -> int:
    started=now()
    prune_results()
    try: request,payloads=read_request()
    except AgentError as exc:
        print(json.dumps({"schema_version":SCHEMA_VERSION,"request_id":"","site":SITE,"site_node":SITE_NODE,
                          "action":"unknown","result":"FAILED","targets":[],"reason":str(exc),"started_at":started,
                          "completed_at":now(),"agent_version":AGENT_VERSION},sort_keys=True)); return 2
    cached=result_path(request["request_id"])
    if cached.is_file() and not cached.is_symlink():
        try:
            value=json.loads(cached.read_text(encoding="utf-8")); print(json.dumps(value,sort_keys=True)); return 0
        except (OSError,json.JSONDecodeError): pass
    try:
        response=HANDLERS[request["action"]](request,payloads)
    except (AgentError,OSError,subprocess.TimeoutExpired,tarfile.TarError) as exc:
        response=base_result(request,"FAILED",reason=str(exc),started=started)
    safe_write_json(cached,response)
    print(json.dumps(response,sort_keys=True))
    return 0 if response["result"] in {"SUCCESS","PARTIAL_SUCCESS","REFUSED"} else 1

if __name__=="__main__":
    raise SystemExit(main())
