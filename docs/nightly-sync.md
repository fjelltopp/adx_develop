# Nightly Prod → Staging Sync

A K8s `CronJob` (`adr-sync` in namespace `adr-s`) refreshes the staging
environment from production every night at 02:00 UTC, while simultaneously
producing dated backups in a dedicated Azure storage account.

## Architecture

```
                ┌─────────────────────────────┐
                │  prod (adr-p)               │
                │                             │
                │  ┌──────────┐ ┌──────────┐  │
                │  │ Postgres │ │   Blob   │  │
                │  │ (ckan,   │ │ adr-p-   │  │
                │  │ datastore)│ │ datalake │  │
                │  └────┬─────┘ └────┬─────┘  │
                │       │            │        │
                │       │  ┌─────────┴──┐     │
                │       │  │ Auth0 prod │     │
                │       │  │ tenant     │     │
                │       │  └────┬───────┘     │
                └───────┼───────┼─────────────┘
                        │       │
            backup phase│       │
                        ▼       ▼
                ┌─────────────────────────────┐
                │  adr-snapshots (Azure Blob) │
                │                             │
                │  postgres/${RUNDATE}/*.dump │
                │  lfs/  (versioned mirror)   │
                │  auth0/${RUNDATE}_users.gz  │
                └─────────────┬───────────────┘
                              │
                  apply phase │
                              ▼
                ┌─────────────────────────────┐
                │  staging (adr-s)            │
                │  ┌──────────┐ ┌──────────┐  │
                │  │ Postgres │ │   Blob   │  │
                │  └──────────┘ └──────────┘  │
                │  ┌────────────────────┐     │
                │  │ Auth0 dev tenant   │     │
                │  │ (users upsert)     │     │
                │  └────────────────────┘     │
                └─────────────────────────────┘
```

Prod is read **once** per night. The staging-apply phase reads exclusively
from `adr-snapshots`. Staging can be re-restored at any time without re-hitting
prod by re-running the apply phase against a chosen `${RUNDATE}`.

The apply phase scales staging `ckan` and `datapusher` deployments to 0
before running `DROP DATABASE`, then scales them back to 1 after the
restores complete. Without this, `DROP DATABASE` fails because the
datapusher's `datastore` Postgres role holds open connections that the
sync (running as `ckan_admin`) cannot terminate. Staging downtime per
nightly run is currently ~2 hours; that's acceptable at 02:00 UTC.

## Auth0 layout

One Auth0 tenant (canonical `dev-udfgla0l.eu.auth0.com`) with the custom
domain `auth-hivtools.unaids.org` promoted on top. The Management API
token endpoint must be hit against the canonical hostname.

Inside the tenant: one SAML SP application per environment (prod CKAN,
staging CKAN) plus one M2M application for adr-sync's nightly users-exports
backup. `user_id` values are tenant-scoped, so the saml_ids in CKAN's
`plugin_extras` already match across environments and `process_user()`'s
saml_id lookup hits immediately after a sync — no users-imports step needed.

## Files

| Path | Purpose |
| ---- | ------- |
| `deploy/sync/sync.py` | Orchestrator (Python). Env-driven. |
| `deploy/sync/Dockerfile.sync` | Built and pushed as `adracr.azurecr.io/adr-sync`. |
| `deploy/sync/cronjob.yaml` | CronJob + ServiceAccount + Role + RoleBinding in `adr-s`. |
| `deploy/sync/secrets.yaml.template` | Shape of `adr-sync-secrets`. Populate locally — **never** commit a real copy. |
| `docs/nightly-sync.md` | This file. |

## One-time setup

### Azure

1. Create the snapshots storage account and container:
   ```bash
   RG="ADR-EUN-01"
   az storage account create --name adrsnapshotsta -g $RG \
       --location northeurope --sku Standard_LRS --kind StorageV2
   az storage account blob-service-properties update --account-name adrsnapshotsta \
       --enable-versioning true
   az storage container create --account-name adrsnapshotsta --name snapshots --auth-mode login
   ```

2. Apply a lifecycle management policy on the storage account so backups
   age out automatically. Example JSON (apply via
   `az storage account management-policy create`):
   - `postgres/` + `auth0/`: cool@30d, archive@60d, delete@365d.
   - `lfs/` old versions: cool@7d, archive@30d, delete@90d.

3. Mint SAS tokens (or use a User Assigned Managed Identity — better, but
   more setup). Minimum SAS scopes:
   - `PROD_LFS_SAS`: read+list on `adr-p-datalake`.
   - `SNAPSHOTS_SAS`: read+list+write+delete on `snapshots`.
   - `STAGING_LFS_SAS`: read+list+write+delete on `adr-s-datalake`.

### Auth0 (dev tenant)

1. In `https://manage.auth0.com` (dev tenant `dev-udfgla0l`), create a
   Machine-to-Machine Application authorised against the Auth0 Management API.
   Required scopes: `create:users`, `update:users`, `read:users`,
   `read:connections`.

2. From a shell with the new M2M creds, find the dev tenant's
   SAML/DB connection ID:
   ```bash
   TOKEN=$(curl -s -X POST https://dev-udfgla0l.eu.auth0.com/oauth/token \
       -H 'content-type: application/x-www-form-urlencoded' \
       -d "grant_type=client_credentials&client_id=$CID&client_secret=$CSEC&audience=https://dev-udfgla0l.eu.auth0.com/api/v2/" \
       | jq -r .access_token)
   curl -s "https://dev-udfgla0l.eu.auth0.com/api/v2/connections" \
       -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, name, strategy}'
   ```
   Note the `id` of the relevant connection (`samlp` strategy for the
   federated UNAIDS-style logins, or the Username-Password-Authentication
   default DB connection if the dev tenant accepts password logins too).

### Kubernetes

1. Build & push the sync image:
   ```bash
   docker build --platform linux/amd64 -t adracr.azurecr.io/adr-sync:latest \
       -f deploy/sync/Dockerfile.sync deploy/sync
   docker push adracr.azurecr.io/adr-sync:latest
   ```

2. Populate a local copy of `deploy/sync/secrets.yaml.template` with real
   values, then:
   ```bash
   kubectl apply -f secrets.yaml.local      # NOT the template
   kubectl apply -f deploy/sync/cronjob.yaml
   ```

   `cronjob.yaml` provisions a `Role` granting the `adr-sync`
   ServiceAccount `patch` on `deployments` and `deployments/scale` so
   the apply phase can scale `ckan` + `datapusher` to 0 and back, plus
   `pods/exec` for the search-index rebuild step.

## Operations

### Manual one-off run

```bash
kubectl create job --from=cronjob/adr-sync adr-sync-manual-$(date +%s) -n adr-s
kubectl logs -f -l job-name=adr-sync-manual-... -n adr-s
```

### Force a specific backup date for the apply phase

By default the script generates `RUNDATE` from the current UTC date. To
restore staging from an older snapshot, set `RUNDATE` and disable the backup
half by tweaking the manifest (or run `sync.py` directly with
`--skip-backup` — TODO if needed). For now, the simplest path is to copy
the desired date's blobs into today's path before running.

### Cleaning up

`adr-snapshots` retention is driven by the lifecycle policy — no manual
cleanup needed for routine operation.

### Failure modes

| Symptom | Likely cause | Fix |
| ------- | ------------ | --- |
| `pg_dump` 28000 auth failed | Postgres password rotated | Update `PROD_CKAN_PG_URL` in `adr-sync-secrets`. |
| `azcopy` 403 AuthenticationFailed | SAS expired | Re-mint SAS, update secret. |
| Auth0 export job times out | Token expired or M2M scope missing | Check tenant logs in Auth0 dashboard. |
| Auth0 import reports per-row errors | Email collisions, malformed `user_id` | See job `/errors`. Often fine to ignore; will retry next night. |
| `ckan search-index rebuild` fails | Solr not ready / Postgres restore incomplete | Check the Solr live-patch state (see `adr-solr-live-patches` memory). |
| Home page returns 500 `Dataset not found` after sync | Reindex ran without `--clear`; stale Solr docs point at deleted DB rows | Re-run `ckan search-index rebuild --force --clear` against staging. |
| `CRITI ckanext.X: requires database setup` after sync | Staging code declares a table that prod's DB doesn't have; the sync wipes staging to prod's schema | The sync's `ckan_migrate` step runs `ckan db upgrade`, then iterates over every plugin in `ckan.plugins` and tries `ckan <plugin> initdb` / `init-db`. Plugins without one are silently skipped. No code change needed for new extensions — just enable them in `ckan.plugins` and the next sync will run their initdb. |
| `pg_restore` reports ~7 ignored errors | 2 real data duplicates in prod (`pages_alembic_version_pkc`, `user_name_key`) + 5 benign duplicate-index entries from ckanext-harvest | Expected. Fix the prod data duplicates separately. |
| `ckan` + `datapusher` stuck at 0 replicas after a failed/killed job | k8s SIGKILL on `activeDeadlineSeconds` bypasses Python's `finally:` | `kubectl scale deploy ckan datapusher --replicas=1 -n adr-s`. |
| Job killed at `activeDeadlineSeconds` | Restore + reindex exceeded 4h | Investigate Postgres / pg_restore slowness; bump deadline if real. |

## Cost

Same-region Azure Blob copy is free (bandwidth $0). Storage all-in:

- Postgres dumps: ~800 MB/day × 30 days hot + 365 days cool/archive → cents/month.
- Auth0 exports: KB-scale; negligible.
- LFS mirror: 50 GB current version + ~1-2% daily delta retained as old
  versions, ageing to cool/archive — under $2/month.

Total: comfortably under $5/month.

## Related work

- Replaces the AWS-era `fjelltopp/adx_toolbox` scripts:
  `sh_scripts/rds_snapshot_restore/sync_development.sh`,
  `sh_scripts/storage_sync/dev_storage_sync.sh`,
  `sh_scripts/backup_scripts/auth0_backup_users.sh`.
- The `auth0_users_db_and_infra_backup.py` Management API patterns are
  reused (copy-adapted) in `deploy/sync/sync.py`.
- The migration pod scripts in `migrate/` use the same k8s Secret sourcing
  pattern for credentials (see `migrate/launch_prod_migration_pod.sh`).
