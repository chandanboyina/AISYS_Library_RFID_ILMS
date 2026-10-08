# D0-D10 Delivery Plan

| Stage | Output |
|---|---|
| D0 | Repo, issue tracker, assumptions, risks, synthetic-data declaration |
| D1 | Requirements package + traceability |
| D2 | Architecture, data, interface and security designs |
| D3 | Foundation: config, auth, RBAC, audit, health, migrations, tests |
| D4 | Cataloguing, members, circulation |
| D5 | Fines/restrictions, search, reports/dashboard |
| D6 | RFID middleware, NCIP/SIP2 mocks, inventory, gate, notification, smart-card/camera mocks |
| D7 | Migration, validation, reconciliation, backup/restore and rollback |
| D8 | Functional/integration/security/performance/UAT evidence |
| D9 | Deployment package, admin/user/API/runbook/training docs |
| D10 | Live/recorded demonstration, known limitations and production backlog |

## Final production-readiness backlog

- Replace mocks with approved vendor SDK/API adapters.
- Confirm actual ILMS schema and integration contract.
- Add real full-text search engine if required by site volume.
- Add migration versioning with Alembic revisions for every schema change.
- Add idempotency keys and durable event queue for RFID events.
- Add enterprise SSO and secrets management.
- Complete performance/security/UAT evidence on target Windows hardware.
- Formalize DR RPO/RTO and monitoring/SIEM integration.
