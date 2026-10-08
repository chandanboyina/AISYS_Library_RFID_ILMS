# Security Package

## Controls implemented

- JWT access tokens with expiry.
- Role-based permissions for admin, librarian and operator.
- Password hashing with bcrypt.
- Environment-based secrets.
- Input validation with Pydantic.
- Audit records for administrative, circulation and RFID-sensitive actions.
- Synthetic data in sample assets.
- No credentials committed to source.
- Dependency versions pinned.

## Threats considered

| Threat | Control |
|---|---|
| Unauthorized circulation | RBAC + member/reference/fine checks |
| Privilege escalation | role checks on admin/library operations |
| Data corruption during migration | staging + validation + transaction + rollback |
| Duplicate RFID events | tag lookup and event model; production backlog should add event idempotency keys |
| Secret leakage | `.env`, no secrets in repo |
| Unauthorized gate removal | gate authorization check + audit + notification queue |
| Supply-chain drift | pinned requirements + dependency inventory |

## Production hardening required

TLS termination, secure password policy/SSO, secret manager, CSRF strategy if cookie auth is introduced, rate limiting, centralized logging/SIEM, vulnerability scanning, database encryption at rest, HA/DR, formal threat model, penetration test, accessibility audit and vendor certification where applicable.
