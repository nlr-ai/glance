#!/bin/bash
# Ensure data directory exists for persistent disk
mkdir -p /var/data 2>/dev/null || true
# Debug: show DB path and disk state
echo "GLANCE_DB_PATH=${GLANCE_DB_PATH:-NOT SET (fallback to /app/data/glance.db)}"
echo "Disk /var/data contents:"
ls -la /var/data/ 2>/dev/null || echo "  /var/data/ does not exist"
# Restore user uploads from persistent disk
if [ -d "/var/data/user_uploads" ]; then
    mkdir -p /app/ga_library/user_uploads
    cp -n /var/data/user_uploads/* /app/ga_library/user_uploads/ 2>/dev/null
    echo "Restored $(ls /var/data/user_uploads/ 2>/dev/null | wc -l) user uploads from persistent disk"
fi
# Initialize DB if needed
python -c "from db import init_db, DB_PATH; print(f'DB_PATH={DB_PATH}'); init_db()"
# Regenerate paper PDF from markdown (if markdown source changed)
python -c "
import os, hashlib, markdown
BASE = os.path.dirname(os.path.abspath('app.py'))
md_path = os.path.join(BASE, 'GLANCE_Paper_Draft.md')
pdf_path = os.path.join(BASE, 'static', 'GLANCE_Paper_Draft.pdf')
html_path = os.path.join(BASE, 'static', 'GLANCE_Paper_Draft.html')
if os.path.exists(md_path):
    with open(md_path, encoding='utf-8') as f:
        md = f.read()
    html = '<html><head><meta charset=\"utf-8\"><style>body{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px;font-size:14px;line-height:1.6}h1{font-size:24px;border-bottom:2px solid #333;padding-bottom:8px}h2{font-size:20px;margin-top:30px;border-bottom:1px solid #ddd}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #ddd;padding:8px}th{background:#f5f5f5}code{background:#f0f0f0;padding:2px 6px;border-radius:3px}pre{background:#f5f5f5;padding:16px;border-radius:6px;overflow-x:auto}</style></head><body>'
    html += markdown.markdown(md, extensions=['tables','fenced_code','toc'])
    html += '</body></html>'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Paper HTML generated: {html_path}')
" 2>/dev/null || echo "Paper generation skipped"
# Start server
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
