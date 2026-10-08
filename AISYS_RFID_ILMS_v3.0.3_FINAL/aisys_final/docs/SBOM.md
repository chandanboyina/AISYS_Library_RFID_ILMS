# Software Bill of Materials (candidate manifest)

This is a human-readable dependency manifest. A production release should generate a machine-readable SPDX/CycloneDX SBOM from the exact built artifact.

| Component | Version | Purpose |
|---|---:|---|
| FastAPI | 0.116.1 | API/web framework |
| Uvicorn | 0.35.0 | ASGI server |
| SQLAlchemy | 2.0.43 | ORM/database abstraction |
| Pydantic | 2.11.7 | validation/schema |
| Pydantic Settings | 2.10.1 | environment configuration |
| Jinja2 | 3.1.6 | server-rendered web UI |
| python-multipart | 0.0.20 | form/file uploads |
| python-jose | 3.5.0 | JWT |
| passlib | 1.7.4 | password hashing interface |
| bcrypt | 4.0.1 | password hashing backend |
| openpyxl | 3.1.5 | XLSX migration |
| psycopg | 3.2.9 | PostgreSQL driver |
| Alembic | 1.16.5 | versioned DB migration boundary |
| httpx | 0.28.1 | API test client support |
| pytest | 8.4.2 | test framework |
