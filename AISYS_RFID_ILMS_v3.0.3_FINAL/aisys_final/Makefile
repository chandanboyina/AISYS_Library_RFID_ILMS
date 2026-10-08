install:
	python -m pip install -r requirements.txt
run:
	uvicorn app.main:app --reload
seed:
	python scripts/seed_demo.py
test:
	pytest -q
acceptance:
	python scripts/acceptance_demo.py
sample:
	python scripts/generate_sample_xlsx.py
migration:
	python scripts/migrate.py sample/library_source_20000.xlsx
