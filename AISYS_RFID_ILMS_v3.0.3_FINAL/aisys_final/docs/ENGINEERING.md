# Engineering Controls

## Git

Use feature branches such as `feature/rfid-gate-events`, reviewed pull requests, meaningful commits and a release tag such as `v1.0.0-candidate`.

## Quality gate

```text
format → lint → static analysis → dependency scan → unit/integration tests → acceptance smoke → package
```

## Change control

A behavior change must update the relevant requirement, design, code, test and documentation. Every defect should record severity, reproduction, owner, status, fix version and retest evidence.
