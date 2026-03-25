#!/bin/bash
# Ensure data directory exists for persistent disk
mkdir -p /var/data 2>/dev/null || true
# Initialize DB if needed
python -c "from db import init_db; init_db()"
# Start server
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
