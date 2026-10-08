# API Guide

Interactive OpenAPI documentation is available at `/docs` when the service is running.

## Authentication

`POST /api/auth/login` with form fields `username` and `password`. Send `Authorization: Bearer <token>` on protected endpoints.

## Main endpoints

- `GET /api/health`
- `GET /api/me`
- `GET/POST /api/books`
- `GET/POST /api/members`
- `POST /api/circulation/checkout`
- `POST /api/circulation/checkin`
- `POST /api/circulation/renew`
- `POST /api/rfid/associate`
- `POST /api/rfid/read`
- `POST /api/rfid/inventory`
- `POST /api/gate/event`
- `POST /api/smart-card/login`
- `POST /api/notifications`
- `POST /api/migration/dry-run`
- `POST /api/migration/import`
- `GET /api/dashboard`
- `GET /api/reports/circulation`
- `GET /api/audit`
- `POST /api/admin/config`

## Mock integration semantics

`NCIP2` and `SIP2` are protocol boundaries, not certification claims. The mock adapters return deterministic protocol-labelled responses so the business workflow can be demonstrated without a vendor endpoint.
