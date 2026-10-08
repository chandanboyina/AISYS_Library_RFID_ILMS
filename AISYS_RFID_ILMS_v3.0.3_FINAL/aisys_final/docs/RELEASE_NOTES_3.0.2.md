# AISYS RFID ILMS v3.0.2 — Catalogue Search/UI Hotfix

## Fixes
- Hardened the catalogue search UI with explicit error handling so API/search failures are surfaced instead of leaving a blank results panel.
- Fixed the catalogue Reset action so it clears the search field before reloading the catalogue.
- Catalogue search now includes ISBN in addition to title, author, accession number and category.
- Catalogue result rows now provide an explicit RFID/detail action instead of rendering an always-empty RFID column marker.

## Verification
- Python AST parsing: PASS for app/scripts/tests.
- Python bytecode compilation: PASS for app/scripts/tests.
- Full pytest must be run in the supplied Windows virtual environment because the release container does not contain the project's optional runtime dependencies.
