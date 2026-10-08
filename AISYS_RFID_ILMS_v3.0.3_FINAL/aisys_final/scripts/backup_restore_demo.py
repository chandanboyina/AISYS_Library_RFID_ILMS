"""AC10 backup/restore drill for the local SQLite deployment."""
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
db = ROOT / "aisys.db"
backups = ROOT / "backups"
backups.mkdir(exist_ok=True)
if not db.exists():
    raise SystemExit("aisys.db not found. Start the application once first.")
backup = backups / f"ac10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
with sqlite3.connect(db) as src, sqlite3.connect(backup) as dst:
    src.backup(dst)
with sqlite3.connect(db) as con:
    before = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    con.execute("CREATE TABLE IF NOT EXISTS _ac10_failure_marker(value TEXT)")
    con.execute("DELETE FROM _ac10_failure_marker")
    con.commit()
with sqlite3.connect(backup) as con:
    assert con.execute("SELECT COUNT(*) FROM books").fetchone()[0] == before
with sqlite3.connect(backup) as src, sqlite3.connect(db) as dst:
    src.backup(dst)
with sqlite3.connect(db) as con:
    after = con.execute("SELECT COUNT(*) FROM books").fetchone()[0]
assert before == after
print("AC10 backup/restore: PASS")
print(f"Book count before={before}, after restore={after}")
print(f"Backup={backup}")
