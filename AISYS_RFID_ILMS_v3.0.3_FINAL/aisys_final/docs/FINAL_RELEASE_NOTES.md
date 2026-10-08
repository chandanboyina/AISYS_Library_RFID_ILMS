# AISYS RFID ILMS v3.0.1 — Final Candidate Release

## Release status

This is the corrected candidate release of the AISYS RFID-enabled ILMS prototype.

### v3.0.1 hotfix
- Fixed a Python f-string quoting error in `app/services/migration.py` that prevented test collection and application startup.
- Re-ran Python AST parsing and bytecode compilation across `app/`, `scripts/`, and `tests/`.
- No Python syntax errors remain in the packaged source.

### Runtime verification
The project should be validated in the target Python 3.11 virtual environment with:

```powershell
python -m pip install -r requirements.txt
python scripts\verify_release.py
pytest -q
```

The final acceptance validation should then exercise AC01–AC10 using the supplied synthetic data and mock adapters.
