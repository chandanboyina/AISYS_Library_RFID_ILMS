# AC01–AC10 Demonstration Runbook

## AC01 Migration
Upload `sample/library_source_20000.xlsx`. Run dry-run first. Show source, valid, invalid and duplicate counts. Then import a clean valid file and show the migration run history and row-level migration records.

## AC02 Catalog + RFID
Create/locate a book. Open the record detail. Validate it at RFID Tagging. Associate a unique tag. Show the tag relationship and last-seen state.

## AC03 Circulation
Use a test member and book. Checkout through NCIP2, renew through SIP2, check-in through NCIP2. Show transaction history and audit events.

## AC04 Restrictions
Demonstrate reference-only rejection, blocked-member rejection and fine-limit rejection. Change the fine limit from Administration and repeat the fine test.

## AC05 Inventory
Enter expected tag UIDs and observed UIDs for a shelf. Demonstrate FOUND, MISSING and UNKNOWN; use a different expected shelf in the single-read workflow for MISPLACED. Show visible confirmation and the audit event.

## AC06 Security gate
Use an armed tag that is not currently issued. Trigger the gate. Show accession, security bit, mock CCTV reference and queued notification.

## AC07 Smart card + RBAC
Use CARD-ADMIN-01/admin, CARD-LIB-01/librarian or CARD-OP-01/operator. Then log in as operator and attempt an admin-only endpoint; capture HTTP 403.

## AC08 Reports
Show dashboard metrics, circulation report, audit trail, RFID events, gate events and notification queue.

## AC09 Offline lifecycle
Run the offline bundle/host procedure with internet unavailable. Take a pre-update backup, apply a controlled update, roll back and prove health plus key data counts remain intact. Capture terminal output.

## AC10 Backup/restore
Record baseline counts. Take a backup. Simulate a failed migration/integration change. Restore the backup. Re-run the counts and show that the original business records are intact.
