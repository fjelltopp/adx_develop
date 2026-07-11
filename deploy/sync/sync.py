#!/usr/bin/env python3
"""
Nightly prod -> staging sync, doubling as the backup pipeline.

Flow:
    prod -> adr-snapshots (backup phase)
    adr-snapshots -> staging (apply phase)

Each artefact (Postgres dumps, LFS blobs, ckan-storage PV files, Auth0
users) is written to adr-snapshots first, then the staging side reads
from there. Prod is read once per night regardless of how many places
we restore to.
"""
from __future__ import annotations

import base64
import dataclasses
import datetime as dt
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

import requests

log = logging.getLogger("sync")

RUNDATE = os.environ.get("RUNDATE") or dt.datetime.utcnow().strftime("%Y%m%d")


@dataclasses.dataclass
class Config:
    # Postgres — single admin URL per environment (ckan_admin user); the
    # datastore URL is derived by swapping the DB path (same role has perms
    # on both DBs). We deliberately don't use CKAN_DATASTORE_WRITE_URL because
    # that role can't SELECT from the UUID-named resource tables.
    prod_ckan_url: str
    staging_ckan_url: str

    # Storage (snapshots + prod + staging Azure accounts)
    snapshots_account: str
    snapshots_container: str
    snapshots_sas: str
    prod_lfs_account: str
    prod_lfs_container: str
    prod_lfs_sas: str
    staging_lfs_account: str
    staging_lfs_container: str
    staging_lfs_sas: str

    # ckan-storage PV (Azure Files, dynamically-provisioned per-PVC storage
    # account — unlike LFS these aren't named accounts, so account/share
    # come from env too, not hardcoded).
    prod_ckan_storage_account: str
    prod_ckan_storage_share: str
    prod_ckan_storage_sas: str
    staging_ckan_storage_account: str
    staging_ckan_storage_share: str
    staging_ckan_storage_sas: str

    # Auth0 (single shared tenant; we only need export creds for backups)
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str

    # CKAN reindex
    ckan_namespace: str
    ckan_deployment: str

    # DataPusher token rotation
    ckan_jwt_secret: str
    ckan_ini_secret_name: str

    # Slack
    slack_webhook: str | None

    @classmethod
    def from_env(cls) -> "Config":
        def req(name: str) -> str:
            v = os.environ.get(name)
            if not v:
                raise SystemExit(f"missing required env var: {name}")
            return v

        return cls(
            prod_ckan_url=req("PROD_CKAN_PG_URL"),
            staging_ckan_url=req("STAGING_CKAN_PG_URL"),
            snapshots_account=req("SNAPSHOTS_ACCOUNT"),
            snapshots_container=req("SNAPSHOTS_CONTAINER"),
            snapshots_sas=req("SNAPSHOTS_SAS"),
            prod_lfs_account=req("PROD_LFS_ACCOUNT"),
            prod_lfs_container=req("PROD_LFS_CONTAINER"),
            prod_lfs_sas=req("PROD_LFS_SAS"),
            staging_lfs_account=req("STAGING_LFS_ACCOUNT"),
            staging_lfs_container=req("STAGING_LFS_CONTAINER"),
            staging_lfs_sas=req("STAGING_LFS_SAS"),
            prod_ckan_storage_account=req("PROD_CKAN_STORAGE_ACCOUNT"),
            prod_ckan_storage_share=req("PROD_CKAN_STORAGE_SHARE"),
            prod_ckan_storage_sas=req("PROD_CKAN_STORAGE_SAS"),
            staging_ckan_storage_account=req("STAGING_CKAN_STORAGE_ACCOUNT"),
            staging_ckan_storage_share=req("STAGING_CKAN_STORAGE_SHARE"),
            staging_ckan_storage_sas=req("STAGING_CKAN_STORAGE_SAS"),
            auth0_domain=req("AUTH0_PROD_DOMAIN"),
            auth0_client_id=req("AUTH0_PROD_CLIENT_ID"),
            auth0_client_secret=req("AUTH0_PROD_CLIENT_SECRET"),
            ckan_namespace=os.environ.get("CKAN_NAMESPACE", "adr-s"),
            ckan_deployment=os.environ.get("CKAN_DEPLOYMENT", "deploy/ckan"),
            ckan_jwt_secret=req("CKAN_JWT_SECRET"),
            ckan_ini_secret_name=os.environ.get("CKAN_INI_SECRET_NAME", "ckan-ini-secrets"),
            slack_webhook=os.environ.get("SLACK_WEBHOOK_URL"),
        )


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log.info("$ %s", " ".join(c if not _is_secret(c) else "<redacted>" for c in cmd))
    try:
        return subprocess.run(cmd, check=True, **kw)
    except subprocess.CalledProcessError as e:
        # Rebuild the exception so the traceback doesn't echo redacted args.
        scrubbed = [c if not _is_secret(c) else "<redacted>" for c in e.cmd]
        raise subprocess.CalledProcessError(e.returncode, scrubbed) from None


def _is_secret(s: str) -> bool:
    return any(k in s for k in ("postgresql://", "?sv=", "client_secret"))


def pg_env(url: str, db_override: str | None = None) -> dict[str, str]:
    """Convert a postgresql:// URL into libpq env vars so creds never appear
    on the subprocess command line (and therefore never end up in
    CalledProcessError tracebacks)."""
    u = urllib.parse.urlsplit(url)
    env = dict(os.environ)
    env["PGHOST"] = u.hostname or ""
    if u.port:
        env["PGPORT"] = str(u.port)
    if u.username:
        env["PGUSER"] = urllib.parse.unquote(u.username)
    if u.password:
        env["PGPASSWORD"] = urllib.parse.unquote(u.password)
    env["PGDATABASE"] = db_override or (u.path.lstrip("/") if u.path else "")
    # Azure Postgres Flexible Server requires TLS.
    env.setdefault("PGSSLMODE", "require")
    return env


def slack(cfg: Config, text: str, level: str = "INFO") -> None:
    if not cfg.slack_webhook:
        return
    payload = {"text": f"[adr-sync {RUNDATE}] [{level}] {text}"}
    try:
        requests.post(cfg.slack_webhook, json=payload, timeout=10)
    except Exception as e:
        log.warning("slack notify failed: %s", e)


# ---------- Postgres ----------

def pg_dump_to_blob(cfg: Config, admin_url: str, db_name: str) -> str:
    """pg_dump custom format, then upload to snapshots. db_name overrides the
    DB component of admin_url so the same admin role can dump both ckan and
    datastore. Set SKIP_PG_BACKUP=1 to reuse an existing dump for this RUNDATE
    (useful when iterating on later pipeline stages)."""
    blob_path = f"postgres/{RUNDATE}/{db_name}.dump"
    if os.environ.get("SKIP_PG_BACKUP") == "1":
        log.info("SKIP_PG_BACKUP=1: reusing existing %s without re-dumping", blob_path)
        return blob_path
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{blob_path}?{cfg.snapshots_sas}"
    )
    with tempfile.NamedTemporaryFile(suffix=f".{db_name}.dump", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        run(
            ["pg_dump", "-Fc", "--no-owner", "--no-privileges", "-f", tmp_path],
            env=pg_env(admin_url, db_override=db_name),
        )
        run(["azcopy", "copy", tmp_path, blob_url, "--overwrite=true"])
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
    log.info("postgres %s dumped to %s", db_name, blob_path)
    return blob_path


def _assert_staging_url(admin_url: str) -> None:
    """Refuse destructive DB operations against anything but staging.
    Staging Azure Postgres host is adr-s-eun-db001; the `-s-` segment is
    the marker."""
    host = urllib.parse.urlsplit(admin_url).hostname or ""
    if "-s-" not in host:
        raise RuntimeError(f"refusing to drop database on non-staging host {host!r}")


def _drop_and_recreate_db(admin_url: str, db_name: str) -> None:
    """Terminate sessions on db_name then DROP + CREATE it. Run against the
    `postgres` meta-DB on the same server.

    We don't use `DROP DATABASE ... WITH (FORCE)` because it requires
    pg_signal_backend, which Azure Flexible Server doesn't grant to
    non-admin roles like ckan_admin. The terminate filter `usename =
    current_user` only kills sessions we own; an Azure system superuser
    session on `ckan` would otherwise refuse termination and abort the
    whole DROP. main() scales CKAN + datapusher to 0 before this runs
    so the only sessions left are stragglers from monitoring / extension
    workers.

    Each statement is its own -c invocation: DROP/CREATE DATABASE cannot
    run inside a transaction, and psql wraps multi-statement -c in one."""
    _assert_staging_url(admin_url)
    log.info("dropping and recreating database %s on staging", db_name)
    run(
        ["psql", "-v", "ON_ERROR_STOP=1",
         "-c", (
             f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
             f"WHERE datname = '{db_name}' AND pid <> pg_backend_pid() "
             f"AND usename = current_user;"
         ),
         "-c", f'DROP DATABASE IF EXISTS "{db_name}";',
         "-c", f'CREATE DATABASE "{db_name}";'],
        env=pg_env(admin_url, db_override="postgres"),
    )
def _scale(cfg: Config, deployments: list[str], replicas: int) -> None:
    """Scale staging deployments. Used to stop CKAN + datapusher before
    DROP DATABASE so their connections don't block it. datapusher
    connects to Postgres as a different role (`datastore`) than the
    sync runs as (`ckan_admin`), so we can't terminate its sessions
    from inside the sync — scaling it to 0 is the only way to clear
    them. On scale-up we don't wait; the sync moves on and the pods
    come back in parallel with the rest of the apply phase."""
    for name in deployments:
        run(["kubectl", "scale", "deployment", name,
             f"--replicas={replicas}", "-n", cfg.ckan_namespace])
    if replicas == 0:
        for name in deployments:
            run(["kubectl", "wait", f"--for=delete", "pod",
                 "-l", f"app={name}", "-n", cfg.ckan_namespace, "--timeout=120s"])


def pg_restore_from_blob(cfg: Config, blob_path: str, admin_url: str, db_name: str) -> None:
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{blob_path}?{cfg.snapshots_sas}"
    )
    with tempfile.NamedTemporaryFile(suffix=f".{db_name}.dump", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        run(["azcopy", "copy", blob_url, tmp_path, "--overwrite=true"])

        # Drop and recreate the target database so pg_restore lands on a
        # genuinely empty DB. Avoids the 22-minute serial DROP phase that
        # --clean --if-exists would otherwise spend on thousands of
        # UUID-named datastore tables, and the lock/memory pressure that a
        # single DROP SCHEMA CASCADE causes.
        _drop_and_recreate_db(admin_url, db_name)

        # pg_restore requires -d/--dbname on the command line (PGDATABASE
        # alone is not sufficient).
        # Single-threaded restore — parallel jobs OOM the staging Postgres
        # building large indexes (the `activity` table PK alone needs ~24MB
        # work_mem; 3 workers in parallel blow the budget).
        # pg_restore exits 1 if ANY error occurred. In practice the prod
        # dump throws a handful of benign errors per restore: duplicate
        # CREATE INDEX statements from plugins that register the same
        # index twice (ckanext-harvest), plus a couple of real data
        # duplicates (pages_alembic_version_pkc, user_name_key) that
        # predate the migration. Match the AWS-era behaviour: log loudly
        # but keep going — aborting here would skip the datastore restore
        # and reindex that follow.
        result = subprocess.run(
            ["pg_restore", "--no-owner", "--no-privileges",
             "-d", db_name, tmp_path],
            env=pg_env(admin_url, db_override=db_name),
        )
        if result.returncode != 0:
            log.warning(
                "pg_restore for %s exited %d — see job stderr for per-row errors",
                db_name, result.returncode,
            )
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


# ---------- LFS ----------

def _blob_url(account: str, container: str, sas: str, prefix: str = "") -> str:
    """Build an azcopy-friendly blob URL. Trailing slash on the path forces
    azcopy to treat the target as a directory."""
    path = container.rstrip("/")
    if prefix:
        path = f"{path}/{prefix.strip('/')}/"
    else:
        path = f"{path}/"
    return f"https://{account}.blob.core.windows.net/{path}?{sas}"


def _file_share_url(account: str, share: str, sas: str, prefix: str = "") -> str:
    """Build an azcopy-friendly Azure Files URL. Mirrors _blob_url()."""
    path = share.rstrip("/")
    if prefix:
        path = f"{path}/{prefix.strip('/')}/"
    else:
        path = f"{path}/"
    return f"https://{account}.file.core.windows.net/{path}?{sas}"


def azcopy_sync(src_url: str, dst_url: str) -> None:
    # delete-destination=true to mirror; recursive is default for sync
    run(["azcopy", "sync", src_url, dst_url, "--delete-destination=true"])


# ---------- Auth0 ----------

def auth0_token(domain: str, client_id: str, client_secret: str) -> str:
    """Get an Auth0 Management API M2M token."""
    r = requests.post(
        f"https://{domain}/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{domain}/api/v2/",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def auth0_export_users(cfg: Config) -> str:
    """Create an export job, poll for completion, download users.json.gz, upload to snapshots."""
    token = auth0_token(cfg.auth0_domain, cfg.auth0_client_id, cfg.auth0_client_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    fields = [
        {"name": k} for k in (
            "app_metadata", "blocked", "created_at", "email", "email_verified",
            "family_name", "given_name", "identities", "name", "nickname",
            "user_id", "user_metadata", "username",
        )
    ]
    r = requests.post(
        f"https://{cfg.auth0_domain}/api/v2/jobs/users-exports",
        headers=headers, json={"format": "json", "fields": fields}, timeout=30,
    )
    r.raise_for_status()
    job_id = r.json()["id"]
    log.info("auth0 export job created: %s", job_id)

    download_url = _poll_job(cfg.auth0_domain, token, job_id)
    blob_path = f"auth0/{RUNDATE}_users.json.gz"
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{blob_path}?{cfg.snapshots_sas}"
    )

    with tempfile.NamedTemporaryFile(suffix=".users.json.gz", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        urllib.request.urlretrieve(download_url, tmp_path)
        run(["azcopy", "copy", tmp_path, blob_url, "--overwrite=true"])
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
    return blob_path


def _poll_job(domain: str, token: str, job_id: str, timeout_s: int = 600) -> str:
    """Poll an Auth0 job until completed; return location (for exports) or raise."""
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(f"https://{domain}/api/v2/jobs/{job_id}", headers=headers, timeout=30)
        r.raise_for_status()
        body = r.json()
        status = body.get("status")
        if status == "completed":
            return body.get("location", "")
        if status == "failed":
            raise RuntimeError(f"auth0 job {job_id} failed: {body}")
        time.sleep(5)
    raise RuntimeError(f"auth0 job {job_id} timed out after {timeout_s}s")


# ---------- CKAN ----------

def ckan_migrate(cfg: Config) -> None:
    """Run CKAN core + per-extension migrations against the freshly-
    restored DB. The AWS-era sync didn't do this — staging code is often
    ahead of prod's schema and a raw data-copy leaves new extensions
    complaining at boot until each runs its initdb.

    Core alembic runs once (`ckan db upgrade`). After that we discover
    enabled plugins from `ckan.plugins` in the live config and try each
    one's `initdb` / `init-db` subcommand. Most plugins don't have one —
    those exit code 2 (Click "no such command") and we swallow silently.
    This way a new extension that needs initdb works without editing
    sync.py."""
    _ckan_exec(cfg, ["db", "upgrade"])

    plugins = _enabled_plugins(cfg)
    log.info("post-restore: probing %d plugins for initdb", len(plugins))
    for plugin in plugins:
        for sub in ("initdb", "init-db"):
            rc = _ckan_exec(cfg, [plugin, sub], quiet_codes={2})
            if rc == 0:
                break  # this plugin's initdb succeeded; don't try the other variant


def _ckan_exec(cfg: Config, args: list[str], quiet_codes: set[int] | None = None) -> int:
    """Run `ckan -c /tmp/production.ini <args>` inside the CKAN pod.
    Returns the exit code. Logs a warning on non-zero unless the code
    is in quiet_codes (e.g. {2} for "no such Click subcommand")."""
    result = subprocess.run(
        ["kubectl", "exec", "-n", cfg.ckan_namespace, cfg.ckan_deployment, "--",
         "ckan", "-c", "/tmp/production.ini", *args],
        check=False,
    )
    if result.returncode != 0 and (not quiet_codes or result.returncode not in quiet_codes):
        log.warning("ckan %s exited %d", " ".join(args), result.returncode)
    return result.returncode


def _enabled_plugins(cfg: Config) -> list[str]:
    """Parse the `ckan.plugins =` value from /tmp/production.ini inside the
    CKAN pod and return the plugin names. The value spans multiple lines
    using ConfigParser-style indentation (see deploy/base.ini), so we
    capture the first match line and any following indented continuation
    lines until the next non-indented line or EOF."""
    awk_prog = (
        r'/^ckan\.plugins[[:space:]]*=/ {sub(/^[^=]*=/, ""); print; in_val=1; next}'
        r' in_val && /^[[:space:]]/ {print; next}'
        r' in_val {exit}'
    )
    result = subprocess.run(
        ["kubectl", "exec", "-n", cfg.ckan_namespace, cfg.ckan_deployment, "--",
         "awk", awk_prog, "/tmp/production.ini"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.split()


def grant_datastore_permissions(cfg: Config) -> None:
    """Re-apply datastore role GRANTs after restore.

    pg_restore runs with --no-privileges, which strips every GRANT from
    the restored datastore DB. The datastore_ro role then can't SELECT
    from _table_metadata, so DataPusher's `datastore_search` call 500s,
    push_to_datastore aborts before it pushes any rows, and the
    `complete` callback that creates datatables_view never fires —
    uploads succeed but views don't appear.

    `ckan datastore set-permissions` prints the canonical GRANT script
    to stdout; we pipe it into psql as ckan_admin against the datastore
    DB."""
    result = subprocess.run(
        ["kubectl", "exec", "-n", cfg.ckan_namespace, cfg.ckan_deployment, "--",
         "ckan", "-c", "/tmp/production.ini", "datastore", "set-permissions"],
        capture_output=True, text=True, check=True,
    )
    run(
        ["psql", "-v", "ON_ERROR_STOP=1"],
        env=pg_env(cfg.staging_ckan_url, db_override="datastore"),
        input=result.stdout, text=True,
    )


def ckan_reindex(cfg: Config) -> None:
    # CKAN config is merged at startup to /tmp/production.ini
    # (base.ini + env.ini + secrets.ini); see deploy/base.ini.
    # --clear wipes Solr before reindexing. Without it, datasets that
    # existed in staging Solr but not in the freshly-restored DB linger
    # in the index; `package_search` then returns IDs that the ckanext-
    # restricted plugin tries to load from the DB, raising ObjectNotFound
    # and 500-ing the home page.
    # --force skips datasets that fail to serialize (a CKAN-level data
    # quirk, not a sync issue) instead of aborting. One known per-dataset
    # failure: a dataset whose `config` field exceeds Solr's 32766-byte
    # max term length — that one stays out of the index.
    result = subprocess.run(
        [
            "kubectl", "exec", "-n", cfg.ckan_namespace, cfg.ckan_deployment, "--",
            "ckan", "-c", "/tmp/production.ini", "search-index", "rebuild", "--force", "--clear",
        ],
        check=False,
    )
    if result.returncode != 0:
        log.warning("ckan search-index rebuild exited %d — check logs for per-dataset failures", result.returncode)


# ---------- DataPusher token rotation ----------

def _make_api_token(jwt_secret: str) -> tuple[str, str]:
    """Generate a CKAN-compatible HS256 JWT API token.

    Replicates what `ckan user token add` produces: header.payload.sig with
    no expiry claim.  The jti is the DB row ID; the token string is what goes
    in ckan.datapusher.api_token.

    Returns (jti, token_string).
    """
    jti = secrets.token_urlsafe(48)
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(
        json.dumps({"jti": jti, "iat": int(time.time())}, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    msg = f"{header}.{payload}"
    sig = hmac.new(jwt_secret.encode(), msg.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return jti, f"{msg}.{sig_b64}"


def refresh_datapusher_token(cfg: Config) -> None:
    """Regenerate the DataPusher API token after a DB restore.

    The nightly sync replaces staging's DB with a prod snapshot. Any token
    previously stored only in staging's api_token table is wiped, breaking
    DataPusher's ability to call back to CKAN. This function:

      1. Generates a fresh JWT using the same secret CKAN uses.
      2. Inserts a matching row into the restored staging DB.
      3. Patches ckan-ini-secrets with the new token value.

    Called inside the scale-to-0 window, before CKAN scales back up, so the
    pod starts with a token that already exists in the DB.
    """
    jti, token = _make_api_token(cfg.ckan_jwt_secret)

    run(
        ["psql", "-v", "ON_ERROR_STOP=1",
         "-c", "DELETE FROM api_token WHERE name = 'datapusher_staging';",
         "-c", (
             f"INSERT INTO api_token (id, name, user_id) "
             f"SELECT '{jti}', 'datapusher_staging', id "
             f"FROM public.user WHERE name = 'admin' LIMIT 1;"
         )],
        env=pg_env(cfg.staging_ckan_url),
    )

    result = subprocess.run(
        ["kubectl", "get", "secret", cfg.ckan_ini_secret_name,
         "-n", cfg.ckan_namespace, "-o", "jsonpath={.data.secrets\\.ini}"],
        capture_output=True, text=True, check=True,
    )
    current_ini = base64.b64decode(result.stdout.strip()).decode()
    new_ini = re.sub(
        r"(?m)^ckan\.datapusher\.api_token\s*=.*$",
        f"ckan.datapusher.api_token = {token}",
        current_ini,
    )
    if new_ini == current_ini:
        log.warning("refresh_datapusher_token: ckan.datapusher.api_token not found in secrets.ini — skipping patch")
        return
    new_b64 = base64.b64encode(new_ini.encode()).decode()
    run(
        ["kubectl", "patch", "secret", cfg.ckan_ini_secret_name,
         "-n", cfg.ckan_namespace, "--type=merge",
         "-p", json.dumps({"data": {"secrets.ini": new_b64}})],
    )
    log.info("datapusher api token refreshed (jti=%s…)", jti[:16])


# ---------- main ----------

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.from_env()
    slack(cfg, "sync starting")

    try:
        # Backup phase
        log.info("=== backup phase ===")
        ckan_dump = pg_dump_to_blob(cfg, cfg.prod_ckan_url, "ckan")
        ds_dump = pg_dump_to_blob(cfg, cfg.prod_ckan_url, "datastore")
        azcopy_sync(
            _blob_url(cfg.prod_lfs_account, cfg.prod_lfs_container, cfg.prod_lfs_sas),
            _blob_url(cfg.snapshots_account, cfg.snapshots_container, cfg.snapshots_sas, prefix="lfs"),
        )
        azcopy_sync(
            _file_share_url(cfg.prod_ckan_storage_account, cfg.prod_ckan_storage_share, cfg.prod_ckan_storage_sas),
            _blob_url(cfg.snapshots_account, cfg.snapshots_container, cfg.snapshots_sas, prefix="ckan-storage"),
        )
        auth0_export_users(cfg)
        slack(cfg, "backup phase done")

        # Apply phase
        log.info("=== apply phase ===")
        # Scale CKAN + datapusher to 0 so DROP DATABASE on staging isn't
        # blocked. finally: scale back regardless of restore outcome, but
        # note that k8s SIGKILL on activeDeadlineSeconds bypasses finally
        # — if the job is killed mid-restore, ckan + datapusher need
        # manual `kubectl scale --replicas=1` to come back.
        scaled = ["ckan", "datapusher"]
        try:
            _scale(cfg, scaled, 0)
            pg_restore_from_blob(cfg, ckan_dump, cfg.staging_ckan_url, "ckan")
            pg_restore_from_blob(cfg, ds_dump, cfg.staging_ckan_url, "datastore")
            refresh_datapusher_token(cfg)
        finally:
            _scale(cfg, scaled, 1)
        azcopy_sync(
            _blob_url(cfg.snapshots_account, cfg.snapshots_container, cfg.snapshots_sas, prefix="lfs"),
            _blob_url(cfg.staging_lfs_account, cfg.staging_lfs_container, cfg.staging_lfs_sas),
        )
        azcopy_sync(
            _blob_url(cfg.snapshots_account, cfg.snapshots_container, cfg.snapshots_sas, prefix="ckan-storage"),
            _file_share_url(cfg.staging_ckan_storage_account, cfg.staging_ckan_storage_share, cfg.staging_ckan_storage_sas),
        )
        ckan_migrate(cfg)
        grant_datastore_permissions(cfg)
        ckan_reindex(cfg)

        slack(cfg, "sync OK", level="OK")
        return 0
    except Exception as e:
        log.exception("sync failed")
        slack(cfg, f"sync FAILED: {e}", level="ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
