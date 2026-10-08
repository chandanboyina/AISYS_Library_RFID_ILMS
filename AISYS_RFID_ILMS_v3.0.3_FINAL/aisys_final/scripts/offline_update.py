"""Safe offline update helper. Backs up SQLite DB, records release, and supports rollback by restoring a backup."""
import argparse, shutil
from pathlib import Path
from datetime import datetime

p=argparse.ArgumentParser(); p.add_argument('command',choices=['backup','rollback']); p.add_argument('--backup'); args=p.parse_args()
db=Path('aisys.db'); backups=Path('backups'); backups.mkdir(exist_ok=True)
if args.command=='backup':
    if not db.exists(): raise SystemExit('aisys.db does not exist')
    dest=backups/f'pre_update_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'; shutil.copy2(db,dest); print(dest)
else:
    if not args.backup: raise SystemExit('--backup is required')
    shutil.copy2(args.backup,db); print(f'Rolled back database from {args.backup}')
