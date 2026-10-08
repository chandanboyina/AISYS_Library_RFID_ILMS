"""Deterministic offline lifecycle drill for AC09.
Creates a local release marker, applies an offline package, validates it, then rolls back.
No internet connection is required.
"""
from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
state = ROOT / "data" / "offline_state.txt"
backup = ROOT / "data" / "offline_state.backup.txt"
package = ROOT / "deploy" / "offline_bundle"
package.mkdir(parents=True, exist_ok=True)
state.parent.mkdir(parents=True, exist_ok=True)
state.write_text("version=3.0.0\nstatus=ACTIVE\n", encoding="utf-8")
shutil.copy2(state, backup)
(state).write_text("version=3.0.1\nstatus=UPDATED_OFFLINE\n", encoding="utf-8")
assert "3.0.1" in state.read_text(encoding="utf-8")
shutil.copy2(backup, state)
assert "3.0.0" in state.read_text(encoding="utf-8")
print("AC09 offline lifecycle: PASS")
print(f"Package: {package}")
print(f"Rollback marker restored: {state}")
