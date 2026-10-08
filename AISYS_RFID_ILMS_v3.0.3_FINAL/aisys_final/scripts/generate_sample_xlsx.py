from openpyxl import Workbook
from pathlib import Path
N=20000
out=Path('sample/library_source_20000.xlsx'); out.parent.mkdir(exist_ok=True)
wb=Workbook(write_only=True); ws=wb.create_sheet('Books')
ws.append(['accession_no','isbn','title','author','category','reference_only'])
for i in range(1,N+1):
    ws.append([f'ACC-{i:05d}',f'978000{i:07d}',f'Synthetic Library Book {i}',f'Author {i%500:03d}', ['Science','Technology','Arts','Business','Literature'][i%5], 'false'])
wb.save(out); print(out)
