# Deployment Guide

## Local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Isolated/container deployment

```bash
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up -d
curl http://localhost:8000/api/health
```

For a truly disconnected site, build and export the images on a connected staging machine, transfer image tarballs and source, then `docker load` at the site. Do not pull from the public Internet at the isolated site.

## Windows target

The SOP targets Windows 11 clients and Windows Server 2022 or later. The application is container-friendly; on a Windows Server site use the organization's approved container runtime, or install Python 3.11+ and run the API as a Windows service. Network firewall rules should expose only the required application port to the library LAN.

## Configuration

Set `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS` and environment-specific provider endpoints outside source code. Never commit real credentials.
