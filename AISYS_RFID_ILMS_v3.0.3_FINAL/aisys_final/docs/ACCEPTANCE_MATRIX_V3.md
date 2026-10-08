# AC01–AC10 Evidence Matrix — v3.0.0

| Scenario | Primary workflow | Expected evidence |
|---|---|---|
| AC01 | Migration dry-run/import | source/valid/invalid/duplicate/migrated counts, rejected rows, reconciliation, rollback batch |
| AC02 | Catalogue + RFID | item record, tag UID, relationship, audit event |
| AC03 | Checkout → renew → check-in | protocol NCIP2/SIP2, state changes, audit trail |
| AC04 | Restrictions | reference item, blocked member, fine-limit rejection |
| AC05 | Handheld inventory | shelf, expected/observed, found/misplaced/missing/unknown, confirmation |
| AC06 | Security gate | authorized decision, security bit/offline basis, accession, CCTV ref, notification |
| AC07 | Smart card + RBAC | card mapping, admin/librarian/operator menus, 403 unauthorized action |
| AC08 | Dashboard/reports | metrics, report summary, circulation/audit/RFID/gate data |
| AC09 | Offline lifecycle | no-network install, update marker, health check, rollback marker |
| AC10 | Backup/restore | backup identifier, simulated failure, restored counts/content |

## Claim discipline
Only mark PASS after the candidate captures local evidence. External hardware and institutional ILMS transport remain mocked unless connected and authorized by AISYS.
