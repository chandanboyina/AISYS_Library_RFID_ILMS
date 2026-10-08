import argparse
from app.db.session import SessionLocal
from app.services.migration import dry_run, import_file

p=argparse.ArgumentParser(); p.add_argument('file'); p.add_argument('--import',dest='do_import',action='store_true'); args=p.parse_args()
db=SessionLocal()
run=import_file(db,args.file) if args.do_import else dry_run(db,args.file)
print({k:getattr(run,k) for k in ['id','source_name','source_rows','valid_rows','invalid_rows','duplicate_rows','migrated_rows','status']})
db.close()
