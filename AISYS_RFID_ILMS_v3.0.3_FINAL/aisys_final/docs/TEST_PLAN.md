# Test Package (D6)

## Test levels

1. Unit: validation, policy and adapter behavior.
2. API integration: authentication, library and RFID endpoints.
3. Migration: valid/invalid/duplicate rows, reconciliation, rollback.
4. Security: role enforcement and secret/config checks.
5. Regression: AC01-AC10 smoke flow.
6. Performance: benchmark 20,000-row dry-run/import on the target hardware; record throughput and peak memory.
7. UAT: librarian scenarios and sign-off evidence.

## Run

```bash
pytest -q
python scripts/acceptance_demo.py
```

## Required evidence for evaluation

Capture terminal output, screenshots of the dashboard, API requests/responses for AC02/AC03/AC06/AC07, migration validation/reconciliation reports, backup/restore evidence and the offline update/rollback result.
