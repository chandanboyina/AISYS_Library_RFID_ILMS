# Known limitations and production backlog

## Mocked boundaries

Physical RFID reader/handheld/gate antennas, smart-card hardware, CCTV capture, printer, email/SMS providers and institutional ILMS transport are mocked. The prototype demonstrates the adapter contract and business logic, not physical certification.

## Remaining production work

1. Connect to the target ILMS using vendor-approved NCIP2/SIP2 implementation and perform conformance testing.
2. Integrate certified RFID hardware, security gate and smart-card readers.
3. Replace mock notification/CCTV adapters with site providers.
4. Execute on Windows Server 2022 in the target network.
5. Add signed offline update packages and controlled deployment approval.
6. Add login rate limiting, MFA, token revocation and CSP/advanced hardening.
7. Add full MARC21/authority control, holds, ILL and patron self-service if required by the institution.
8. Complete librarian UAT sign-off, load/soak testing and penetration testing.
9. Run the final AC09 and AC10 drills on the candidate's Windows machine and retain evidence.


## v3.0.0 explicit boundaries
- NCIP 2.0 and SIP2 remain mock adapter boundaries until an institutional endpoint is supplied.
- RFID readers, gates, cameras, smart cards and notification providers are simulated through adapters.
- PostgreSQL deployment is production-shaped; local evaluation defaults to SQLite for offline Windows execution.
- Windows Server 2022, physical device certification, production load/soak testing and penetration testing remain deployment-stage work.
