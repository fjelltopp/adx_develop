# Nightly Prod → Staging Sync

A K8s `CronJob` (`adr-sync` in namespace `adr-s`) refreshes the staging environment from production every night at 01:00 UTC, while simultaneously producing dated backups in a dedicated Azure storage account.

Prod is read **once** per night. The staging-apply phase reads exclusively from `adr-snapshots`. Staging can be re-restored at any time without re-hitting prod by re-running the apply phase against a chosen `${RUNDATE}`.

The apply phase scales staging `ckan` and `datapusher` deployments to 0 before running `DROP DATABASE`, then scales them back to 1 after the restores complete. Staging downtime per nightly run is currently ~2 hours, mostly taken by the `pg_restore` step.

## Auth0 layout

There's one Auth0 tenant (canonical `dev-udfgla0l.eu.auth0.com`) with the custom domain `auth-hivtools.unaids.org` promoted on top.

Inside the tenant: one SAML SP application per environment (prod CKAN, staging CKAN) plus one M2M application for adr-sync's nightly users-exports backup. `user_id` values are tenant-scoped, so the saml_ids in CKAN's `plugin_extras` already match across environments and `process_user()`'s saml_id lookup hits immediately after a sync.

## Files

| Path | Purpose |
| ---- | ------- |
| `deploy/sync/sync.py` | Orchestrator (Python). Env-driven. |
| `deploy/sync/Dockerfile.sync` | Built and pushed as `adracr.azurecr.io/adr-sync`. |
| `deploy/sync/cronjob.yaml` | CronJob + ServiceAccount + Role + RoleBinding in `adr-s`. |
| `deploy/sync/secrets.yaml.template` | Shape of `adr-sync-secrets`. Populate locally — **never** commit a real copy. |
| `docs/nightly-sync.md` | This file. |

## Operations

### Manual one-off run

```bash
kubectl create job --from=cronjob/adr-sync adr-sync-manual-$(date +%s) -n adr-s
kubectl logs -f -l job-name=adr-sync-manual-... -n adr-s
```

### Rotating SAS tokens

The three SAS tokens in `adr-sync-secrets` (`PROD_LFS_SAS`, `SNAPSHOTS_SAS`, `STAGING_LFS_SAS`) were issued with a **365-day** expiry (currently 22-05-2027). Once they expire, `azcopy` calls will fail with `403 AuthenticationFailed` and the nightly job will start dying at the backup or apply phase.

Rotate them like this (one storage account at a time):

```bash
# Pick an expiry one year out, UTC, ISO-8601.
EXPIRY=$(date -u -v+365d +%Y-%m-%dT%H:%MZ)        # macOS
# EXPIRY=$(date -u -d '+365 days' +%Y-%m-%dT%H:%MZ)  # GNU/Linux

# Get an account key (or use --auth-mode login + --as-user for a user-delegation SAS).
KEY=$(az storage account keys list -g ADR-EUN-01 -n adrpdatalake \
        --query '[0].value' -o tsv)

# PROD_LFS_SAS — read + list on the adr-p-datalake container.
az storage container generate-sas \
    --account-name adrpdatalake --name adr-p-datalake \
    --permissions rl --expiry "$EXPIRY" \
    --account-key "$KEY" -o tsv

# SNAPSHOTS_SAS — full r/w/l/d on the snapshots container.
az storage container generate-sas \
    --account-name adrsnapshotsta --name snapshots \
    --permissions rwdl --expiry "$EXPIRY" \
    --account-key "$(az storage account keys list -g ADR-EUN-01 -n adrsnapshotsta --query '[0].value' -o tsv)" \
    -o tsv

# STAGING_LFS_SAS — full r/w/l/d on the adr-s-datalake container.
az storage container generate-sas \
    --account-name adrsdatalake --name adr-s-datalake \
    --permissions rwdl --expiry "$EXPIRY" \
    --account-key "$(az storage account keys list -g ADR-EUN-01 -n adrsdatalake --query '[0].value' -o tsv)" \
    -o tsv
```

Each command prints the bare query-string SAS (no leading `?`). Patch the existing secret in place — don't recreate it, since other keys like `PROD_CKAN_PG_URL` live in the same secret:

```bash
kubectl patch secret adr-sync-secrets -n adr-s \
    --type='json' -p="$(jq -nc \
        --arg prod "$(printf %s "$PROD_SAS" | base64)" \
        --arg snap "$(printf %s "$SNAP_SAS" | base64)" \
        --arg stag "$(printf %s "$STAG_SAS" | base64)" \
        '[
          {op:"replace", path:"/data/PROD_LFS_SAS",     value:$prod},
          {op:"replace", path:"/data/SNAPSHOTS_SAS",    value:$snap},
          {op:"replace", path:"/data/STAGING_LFS_SAS",  value:$stag}
        ]')"
```

### Cleaning up

`adr-snapshots` retention is driven by an Azure Blob lifecycle management policy on the storage account — no manual cleanup needed for routine operation.

The policy has two rules, scoped by blob prefix:

| Prefix | Tier transitions | Delete |
| ------ | ---------------- | ------ |
| `postgres/`, `auth0/` | cool @ 30 days, archive @ 60 days | 365 days |
| `lfs/` (old versions only) | cool @ 7 days, archive @ 30 days | 90 days |

Notes:

- The `lfs/` rule targets **previous versions** only (blob versioning is on for that prefix). The current version of each LFS object stays hot indefinitely — staging needs to read it on every apply phase.
- `postgres/` and `auth0/` blobs are written once per night under `${RUNDATE}/`, so the age clock starts the moment they land.
- "Days" are measured from last modification, per Azure's `daysAfterModificationGreaterThan` semantics.
- View / edit the policy in the portal under `adrsnapshotsta → Data management → Lifecycle management`, or via `az storage account management-policy show -g ADR-EUN-01 --account-name adrsnapshotsta`.

To restore staging from an archived snapshot you must first rehydrate the blob (Azure archive tier is offline — rehydration takes hours). For routine "restore yesterday's prod into staging" workflows you're always in the hot tier, so this only matters for forensic restores older than a month.

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
