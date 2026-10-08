import os, shutil, sqlite3
from datetime import datetime
from pathlib import Path
src=Path('aisys.db'); out=Path('backups'); out.mkdir(exist_ok=True)
if not src.exists(): raise SystemExit('SQLite database not found; for PostgreSQL use pg_dump as documented in docs/OPERATIONS.md')
dst=out/f'aisys_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
with sqlite3.connect(src) as s, sqlite3.connect(dst) as d: s.backup(d)
print(f'Backup created: {dst}')
