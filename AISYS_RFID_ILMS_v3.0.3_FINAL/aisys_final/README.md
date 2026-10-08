# AISYS RFID-enabled Integrated Library Management System (ILMS)

## Evaluation build v3.0.0

A production-oriented **library management prototype** built for the AISYS Candidate Software Development evaluation. The application is deliberately designed to look and behave like an operational ILMS rather than a generic dashboard.

### Main modules

- Dashboard / live operational monitor
- Cataloguing & search
- Public OPAC
- Circulation desk (checkout, renew, check-in)
- Members & fines
- Acquisitions & serials
- RFID tagging station
- Handheld stock verification
- Security gate + CCTV reference + notification queue
- Spreadsheet migration center
- Reports & audit trail
- Administration / roles / configurable fine limits
- Smart-card mock authentication
- Offline backup / rollback helpers

### Architecture

`Browser ILMS` → `FastAPI application services` → `device/ILMS adapter boundaries` → `SQLAlchemy database`

External hardware and institutional ILMS services are intentionally mocked where unavailable, following the AISYS SOP. The prototype does **not** claim vendor, NCIP/SIP2, ISO, OEM, security or performance certification.

### Run on Windows

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest -q
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Demo credentials:

- admin / Admin@12345
- librarian / Librarian@12345
- operator / Operator@12345

### Acceptance demonstration

Run the deterministic API smoke flow:

```powershell
python scripts\acceptance_demo.py
```

Use the UI to execute AC01–AC10 and capture evidence. The repository intentionally distinguishes implemented software from mocked external systems.

### Important evidence boundary

The candidate must execute the final local acceptance drills for migration reconciliation, offline update/rollback and backup/restore and capture screenshots/terminal evidence. The package does not fabricate those results.

## v3 release verification

```powershell
python scripts\verify_release.py
pytest -q
python scripts\acceptance_demo.py
python scripts\offline_lifecycle.py
```

The local UI includes a dedicated offline gate decision toggle, migration rollback action, patron-card personalization endpoint, due-date enquiry, barcode data endpoint, notification dispatch mock and operational readiness checks.
