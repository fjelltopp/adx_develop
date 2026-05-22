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

## Why Auth0 needs special handling

Prod uses Auth0 tenant `auth-hivtools.unaids.org` (UNAIDS-owned). Staging uses
`dev-udfgla0l.eu.auth0.com` (Fjelltopp-owned). SAML subject IDs are
tenant-specific. A raw Postgres restore leaves
`plugin_extras.saml2auth.saml_id` values that don't match anything the dev IdP
will issue, so the `saml_id`-lookup branch of
`ckanext-saml2auth/process_user()` misses every prod user after a sync.

The email-fallback branch heals it on first login — but only if the dev Auth0
tenant already knows the user's email. The sync's Auth0 step takes care of
that: every prod user is upserted into the dev tenant via
`POST /api/v2/jobs/users-imports`. Role-bearing keys in `app_metadata`
(`roles`, `permissions`, `is_sysadmin`, `admin`) are stripped before import
so prod role grants don't leak into staging.

Identity drift: each nightly DB restore clobbers the freshly-written dev
`saml_id`. First login of the next day re-heals it via email-match. Silent,
harmless, but it does mean the `saml_id` fast path is never the steady state
in staging.

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
