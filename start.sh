#!/bin/bash
# Ensure data directory exists for persistent disk
mkdir -p /var/data 2>/dev/null || true
# Debug: show DB path and disk state
echo "GLANCE_DB_PATH=${GLANCE_DB_PATH:-NOT SET (fallback to /app/data/glance.db)}"
echo "Disk /var/data contents:"
ls -la /var/data/ 2>/dev/null || echo "  /var/data/ does not exist"
# Initialize DB if needed
python -c "from db import init_db, DB_PATH; print(f'DB_PATH={DB_PATH}'); init_db()"
# Start server
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
