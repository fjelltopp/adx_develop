#!/usr/bin/env python3
"""
Nightly prod -> staging sync, doubling as the backup pipeline.

Flow:
    prod -> adr-snapshots (backup phase)
    adr-snapshots -> staging (apply phase)

Each artefact (Postgres dumps, LFS blobs, Auth0 users) is written to
adr-snapshots first, then the staging side reads from there. Prod is
read once per night regardless of how many places we restore to.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

import requests

log = logging.getLogger("sync")

RUNDATE = os.environ.get("RUNDATE") or dt.datetime.utcnow().strftime("%Y%m%d")


@dataclasses.dataclass
class Config:
    # Postgres
    prod_ckan_url: str
    prod_datastore_url: str
    staging_ckan_url: str
    staging_datastore_url: str

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

    # Auth0
    auth0_prod_domain: str
    auth0_prod_client_id: str
    auth0_prod_client_secret: str
    auth0_dev_domain: str
    auth0_dev_client_id: str
    auth0_dev_client_secret: str
    auth0_dev_connection_id: str

    # CKAN reindex
    ckan_namespace: str
    ckan_deployment: str

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
            prod_datastore_url=req("PROD_DATASTORE_PG_URL"),
            staging_ckan_url=req("STAGING_CKAN_PG_URL"),
            staging_datastore_url=req("STAGING_DATASTORE_PG_URL"),
            snapshots_account=req("SNAPSHOTS_ACCOUNT"),
            snapshots_container=req("SNAPSHOTS_CONTAINER"),
            snapshots_sas=req("SNAPSHOTS_SAS"),
            prod_lfs_account=req("PROD_LFS_ACCOUNT"),
            prod_lfs_container=req("PROD_LFS_CONTAINER"),
            prod_lfs_sas=req("PROD_LFS_SAS"),
            staging_lfs_account=req("STAGING_LFS_ACCOUNT"),
            staging_lfs_container=req("STAGING_LFS_CONTAINER"),
            staging_lfs_sas=req("STAGING_LFS_SAS"),
            auth0_prod_domain=req("AUTH0_PROD_DOMAIN"),
            auth0_prod_client_id=req("AUTH0_PROD_CLIENT_ID"),
            auth0_prod_client_secret=req("AUTH0_PROD_CLIENT_SECRET"),
            auth0_dev_domain=req("AUTH0_DEV_DOMAIN"),
            auth0_dev_client_id=req("AUTH0_DEV_CLIENT_ID"),
            auth0_dev_client_secret=req("AUTH0_DEV_CLIENT_SECRET"),
            auth0_dev_connection_id=req("AUTH0_DEV_CONNECTION_ID"),
            ckan_namespace=os.environ.get("CKAN_NAMESPACE", "adr-s"),
            ckan_deployment=os.environ.get("CKAN_DEPLOYMENT", "deploy/ckan"),
            slack_webhook=os.environ.get("SLACK_WEBHOOK_URL"),
        )


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log.info("$ %s", " ".join(c if not _is_secret(c) else "<redacted>" for c in cmd))
    return subprocess.run(cmd, check=True, **kw)


def _is_secret(s: str) -> bool:
    return any(k in s for k in ("postgresql://", "?sv=", "client_secret"))


def slack(cfg: Config, text: str, level: str = "INFO") -> None:
    if not cfg.slack_webhook:
        return
    payload = {"text": f"[adr-sync {RUNDATE}] [{level}] {text}"}
    try:
        requests.post(cfg.slack_webhook, json=payload, timeout=10)
    except Exception as e:
        log.warning("slack notify failed: %s", e)


# ---------- Postgres ----------

def pg_dump_to_blob(cfg: Config, pg_url: str, db_label: str) -> str:
    """pg_dump custom format, stream straight to a blob in snapshots."""
    blob_path = f"postgres/{RUNDATE}/{db_label}.dump"
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{blob_path}?{cfg.snapshots_sas}"
    )
    with tempfile.NamedTemporaryFile(suffix=f".{db_label}.dump", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        run(["pg_dump", "-Fc", "--no-owner", "--no-privileges", "-f", tmp_path, pg_url])
        run(["azcopy", "copy", tmp_path, blob_url, "--overwrite=true"])
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
    log.info("postgres %s dumped to %s", db_label, blob_path)
    return blob_path


def pg_restore_from_blob(cfg: Config, blob_path: str, pg_url: str, db_label: str) -> None:
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{blob_path}?{cfg.snapshots_sas}"
    )
    with tempfile.NamedTemporaryFile(suffix=f".{db_label}.dump", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        run(["azcopy", "copy", blob_url, tmp_path, "--overwrite=true"])
        # pg_restore exits non-zero on clean errors when objects don't pre-exist;
        # that's expected with --clean --if-exists. Capture stderr but don't fail
        # the whole sync on it.
        result = subprocess.run(
            [
                "pg_restore", "--clean", "--if-exists", "--no-owner",
                "--no-privileges", "--dbname", pg_url, tmp_path,
            ],
            check=False,
        )
        if result.returncode != 0:
            log.warning(
                "pg_restore %s exited %d (clean errors are expected, verify counts)",
                db_label, result.returncode,
            )
    finally:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass


# ---------- LFS ----------

def azcopy_sync(src_account: str, src_container: str, src_sas: str,
                dst_account: str, dst_container: str, dst_sas: str) -> None:
    src = f"https://{src_account}.blob.core.windows.net/{src_container}?{src_sas}"
    dst = f"https://{dst_account}.blob.core.windows.net/{dst_container}?{dst_sas}"
    # delete-destination=true to mirror; recursive is the default for sync
    run(["azcopy", "sync", src, dst, "--delete-destination=true"])


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
    token = auth0_token(cfg.auth0_prod_domain, cfg.auth0_prod_client_id, cfg.auth0_prod_client_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    fields = [
        {"name": k} for k in (
            "app_metadata", "blocked", "created_at", "email", "email_verified",
            "family_name", "given_name", "identities", "name", "nickname",
            "user_id", "user_metadata", "username",
        )
    ]
    r = requests.post(
        f"https://{cfg.auth0_prod_domain}/api/v2/jobs/users-exports",
        headers=headers, json={"format": "json", "fields": fields}, timeout=30,
    )
    r.raise_for_status()
    job_id = r.json()["id"]
    log.info("auth0 export job created: %s", job_id)

    download_url = _poll_job(cfg.auth0_prod_domain, token, job_id)
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


def auth0_import_users(cfg: Config, export_blob_path: str) -> None:
    """Download export from snapshots, strip role-bearing app_metadata, import into dev tenant."""
    blob_url = (
        f"https://{cfg.snapshots_account}.blob.core.windows.net/"
        f"{cfg.snapshots_container}/{export_blob_path}?{cfg.snapshots_sas}"
    )
    with tempfile.NamedTemporaryFile(suffix=".users.json.gz", delete=False) as tmp_gz:
        gz_path = tmp_gz.name
    run(["azcopy", "copy", blob_url, gz_path, "--overwrite=true"])

    import gzip
    with gzip.open(gz_path, "rt") as f:
        users = json.load(f)

    sanitised = [_sanitise_for_dev(u) for u in users]

    with tempfile.NamedTemporaryFile("w", suffix=".users.json", delete=False) as tmp_json:
        json.dump(sanitised, tmp_json)
        json_path = tmp_json.name

    token = auth0_token(cfg.auth0_dev_domain, cfg.auth0_dev_client_id, cfg.auth0_dev_client_secret)
    with open(json_path, "rb") as fh:
        r = requests.post(
            f"https://{cfg.auth0_dev_domain}/api/v2/jobs/users-imports",
            headers={"Authorization": f"Bearer {token}"},
            files={"users": ("users.json", fh, "application/json")},
            data={
                "connection_id": cfg.auth0_dev_connection_id,
                "upsert": "true",
                "send_completion_email": "false",
            },
            timeout=60,
        )
    r.raise_for_status()
    job_id = r.json()["id"]
    log.info("auth0 import job started on dev tenant: %s (%d users)", job_id, len(sanitised))
    _poll_job(cfg.auth0_dev_domain, token, job_id, timeout_s=1800)

    # Surface errors but don't fail the sync — partial imports are tolerable.
    err = requests.get(
        f"https://{cfg.auth0_dev_domain}/api/v2/jobs/{job_id}/errors",
        headers={"Authorization": f"Bearer {token}"}, timeout=30,
    )
    if err.ok and err.json():
        count = len(err.json())
        log.warning("auth0 import had %d per-row errors; first: %s", count, err.json()[0])
        slack(cfg, f"auth0 import: {count} per-row errors (job {job_id})", level="WARN")

    for p in (gz_path, json_path):
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass


def _sanitise_for_dev(user: dict) -> dict:
    """Strip prod role grants from app_metadata; keep everything else."""
    out = dict(user)
    meta = dict(out.get("app_metadata") or {})
    for k in ("roles", "permissions", "is_sysadmin", "admin"):
        meta.pop(k, None)
    if meta:
        out["app_metadata"] = meta
    else:
        out.pop("app_metadata", None)
    return out


# ---------- CKAN ----------

def ckan_reindex(cfg: Config) -> None:
    run([
        "kubectl", "exec", "-n", cfg.ckan_namespace, cfg.ckan_deployment, "--",
        "ckan", "-c", "/etc/ckan/production.ini", "search-index", "rebuild",
    ])


# ---------- main ----------

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = Config.from_env()
    slack(cfg, "sync starting")

    try:
        # Backup phase
        log.info("=== backup phase ===")
        ckan_dump = pg_dump_to_blob(cfg, cfg.prod_ckan_url, "ckan")
        ds_dump = pg_dump_to_blob(cfg, cfg.prod_datastore_url, "datastore")
        azcopy_sync(
            cfg.prod_lfs_account, cfg.prod_lfs_container, cfg.prod_lfs_sas,
            cfg.snapshots_account, "lfs", cfg.snapshots_sas,
        )
        export_blob = auth0_export_users(cfg)
        slack(cfg, "backup phase done")

        # Apply phase
        log.info("=== apply phase ===")
        pg_restore_from_blob(cfg, ckan_dump, cfg.staging_ckan_url, "ckan")
        pg_restore_from_blob(cfg, ds_dump, cfg.staging_datastore_url, "datastore")
        azcopy_sync(
            cfg.snapshots_account, "lfs", cfg.snapshots_sas,
            cfg.staging_lfs_account, cfg.staging_lfs_container, cfg.staging_lfs_sas,
        )
        auth0_import_users(cfg, export_blob)
        ckan_reindex(cfg)

        slack(cfg, "sync OK", level="OK")
        return 0
    except Exception as e:
        log.exception("sync failed")
        slack(cfg, f"sync FAILED: {e}", level="ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
