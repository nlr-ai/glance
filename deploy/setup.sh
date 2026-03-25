#!/bin/bash
# GLANCE deployment on Hetzner CX22 (4GB RAM, 2 vCPU, Ubuntu 22.04)
set -e

# System
apt update && apt install -y python3.12 python3.12-venv python3-pip nginx certbot python3-certbot-nginx

# App directory
mkdir -p /opt/glance
cd /opt/glance

# Clone or copy files (placeholder — will use rsync from local)
# rsync -avz user@local:/path/to/glance/ /opt/glance/

# Virtual environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download the embedding model (first run only, ~500MB)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')"

# Initialize database
python -c "from db import init_db; init_db(); from app import _seed_images; _seed_images()"

# Systemd service
cat > /etc/systemd/system/glance.service << 'SVCEOF'
[Unit]
Description=GLANCE - SciSense Comprehension Benchmark
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/glance
Environment="PATH=/opt/glance/venv/bin"
ExecStart=/opt/glance/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8751 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable glance
systemctl start glance

# Nginx reverse proxy
cat > /etc/nginx/sites-available/glance << 'NGXEOF'
server {
    listen 80;
    server_name glance.scisense.fr;

    location / {
        proxy_pass http://127.0.0.1:8751;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/glance/static/;
        expires 30d;
    }

    location /ga/ {
        alias /opt/glance/ga_library/;
        expires 30d;
    }
}
NGXEOF

ln -sf /etc/nginx/sites-available/glance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# SSL (after DNS is pointed)
# certbot --nginx -d glance.scisense.fr --non-interactive --agree-tos -m aurore@scisense.fr

echo "GLANCE deployed. Visit http://$(hostname -I | awk '{print $1}'):80"
