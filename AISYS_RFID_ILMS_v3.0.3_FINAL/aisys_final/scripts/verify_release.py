"""Release verification for the AISYS candidate package.
Runs dependency-free repository checks; pytest is the full application test suite.
"""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
required = [
    "app/main.py", "app/static/app.js", "app/static/app.css", "app/templates/index.html",
    "app/adapters/contracts.py", "app/adapters/mocks.py", "scripts/migrate.py",
    "scripts/backup.py", "scripts/offline_update.py", "sample/library_source_20000.xlsx",
    "docs/REQUIREMENTS_TRACEABILITY.md", "docs/ARCHITECTURE.md", "docs/ACCEPTANCE_DEMO.md"
]
missing = [x for x in required if not (ROOT/x).exists()]
if missing:
    raise SystemExit("Missing release artifacts: " + ", ".join(missing))
for p in ROOT.rglob("*.py"):
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
print(f"Release structure: PASS ({len(required)} required artifacts)")
print("Python AST validation: PASS")
print("Run `pytest -q` for application-level verification.")
