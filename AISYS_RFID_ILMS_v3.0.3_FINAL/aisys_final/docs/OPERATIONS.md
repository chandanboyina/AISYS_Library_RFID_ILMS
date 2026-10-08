# Operations / Runbook

## Health

`GET /api/health` must return `status=UP` and `database=UP`.

## Backup

SQLite demo:

```bash
python scripts/backup.py
```

PostgreSQL deployment:

```bash
docker compose -f deploy/docker-compose.yml exec -T db pg_dump -U aisys -d aisys > backups/aisys.sql
```

## Restore PostgreSQL

```bash
cat backups/aisys.sql | docker compose -f deploy/docker-compose.yml exec -T db psql -U aisys -d aisys
```

Perform restore in a controlled maintenance window and verify `/api/health` plus row counts afterward.

## Offline update

1. Verify release checksum and dependency inventory.
2. Back up database.
3. Stage new image/source package.
4. Apply database migrations if present.
5. Start new release.
6. Run health and acceptance smoke tests.
7. If failed, stop new release and restore the previous package/database backup.

For SQLite demos: `python scripts/offline_update.py backup` and `python scripts/offline_update.py rollback --backup <file>`.

## Incident diagnostics

Collect: release version, health result, container/service logs, last successful audit events, migration run ID, database backup timestamp and reproduction steps. Never collect or paste passwords, tokens, private keys or real personal data into issue trackers.
