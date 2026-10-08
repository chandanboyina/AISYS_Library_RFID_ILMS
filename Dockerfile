# AISYS RFID ILMS — Render deployment image
# The application lives in AISYS_RFID_ILMS_v3.0.3_FINAL/aisys_final.
# This root Dockerfile lets Render build the repository without requiring
# a Dockerfile inside the nested application directory.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first for better Docker layer caching.
COPY AISYS_RFID_ILMS_v3.0.3_FINAL/aisys_final/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Copy the complete AISYS application into the container root.
COPY AISYS_RFID_ILMS_v3.0.3_FINAL/aisys_final/ ./

EXPOSE 8000

# Render supplies PORT at runtime. Fall back to 8000 for local Docker runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
