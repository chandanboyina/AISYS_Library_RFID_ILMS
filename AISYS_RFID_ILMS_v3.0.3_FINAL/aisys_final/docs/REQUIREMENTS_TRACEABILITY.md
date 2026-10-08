# AISYS ILMS Requirements Traceability Matrix

| ID | Requirement | Delivered / evidence |
|---|---|---|
| FR01 | Core ILMS | Cataloguing, OPAC, virtual shelf, acquisitions, serials, circulation, members, fines, reports, RFID workflows |
| FR02 | Web/search | Staff ILMS console, public OPAC, title/author/accession/category search and virtual bookshelf API |
| FR03 | RFID interoperability | Device-neutral contracts plus mock staff reader, handheld reader, gate, smart card, camera, printer and notification adapters; NCIP2/SIP2 boundaries |
| FR04 | Circulation | Checkout, check-in, renewal, due dates, reference restriction, member block, configurable fine limit and RBAC |
| FR05 | Tagging | Record validation before association, duplicate tag protection, tag relationship and last-seen monitoring |
| FR06 | Inventory | Bulk handheld reads, FOUND/MISPLACED/UNKNOWN classification and visible confirmation; browser UI is the visible confirmation surface |
| FR07 | Security gate | Online authorization, security-bit decision input, accession capture, mock CCTV reference, notification queue and gate history |
| FR08 | Dashboard/reports | Live operational dashboard, circulation report, audit report, RFID/gate/notification views and management metrics |
| FR09 | Notifications | Provider-neutral queue and mock email adapter; production providers remain an integration boundary |
| FR10 | Data migration | CSV/XLSX staging, invalid/duplicate detection, row-level migration records, transactional import, migration history and rollback status |
| FR11 | Administration | User/role display, configurable fine/loan parameters, JWT/RBAC, audit log, version/health information |
| FR12 | Offline lifecycle | Windows launcher, Docker deployment, offline bundle notes, SQLite backup and rollback helper; production signed-update orchestration remains backlog |
| NFR01 | Data integrity | Transactions, duplicate controls, backup before controlled changes, restore procedure |
| NFR02 | Security/privacy | bcrypt, JWT, role checks, validation, audit logging, environment configuration and synthetic data |
| NFR03 | Compatibility | Windows 11 local run, Python 3.11, Docker/Compose with PostgreSQL option |
| NFR04 | Licensing | Pinned requirements and SBOM/licensing notes |
| NFR05 | Testability | Pytest API/RBAC/RFID/circulation plus extended ILMS endpoint/configuration tests and acceptance smoke script |
| NFR06 | Maintainability | Adapter boundaries, service layer, typed schemas, Alembic baseline, configuration outside code |
| NFR07 | Supportability | Health endpoint, structured operational documentation and audit/event history |
| NFR08 | Documentation | Architecture, deployment, admin, user, training, security, operations, acceptance and traceability docs |
| NFR09 | Delivery | D0–D10 delivery plan, acceptance procedures, known limitations and production backlog |

## Priority acceptance scenarios

| AC | Demonstration |
|---|---|
| AC01 | Migration Center: upload XLSX/CSV → dry-run → invalid/duplicate rows → import → migration history/reconciliation |
| AC02 | Cataloguing & RFID Tagging: locate item → validate → associate tag → display tag-to-item relationship |
| AC03 | Circulation Desk: NCIP2 checkout → SIP2 renewal → NCIP2 check-in → audit history |
| AC04 | Members & Fines: reference-only, blocked member and configurable fine-limit rejection |
| AC05 | Handheld Inventory: bulk tag reads → FOUND/MISPLACED/UNKNOWN → visible confirmation |
| AC06 | Security Gate: unauthorized tag → accession → CCTV reference → queued notification |
| AC07 | Smart-card mock + admin/librarian/operator RBAC; unauthorized administration returns 403 |
| AC08 | Dashboard, circulation/audit reports, RFID/gate/notification activity |
| AC09 | Offline deployment assets, backup, update/rollback procedure; local evidence required for final claim |
| AC10 | Backup/restore procedure and transactional migration rollback; local restore drill required for final evidence |
