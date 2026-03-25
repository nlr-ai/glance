#!/bin/bash
# Push GLANCE to Hetzner VPS
# Usage: ./rsync_deploy.sh user@ip
set -e
TARGET=${1:-root@your-vps-ip}

rsync -avz --exclude '__pycache__' \
           --exclude 'data/*.db' \
           --exclude '.git' \
           --exclude 'exports/' \
           --exclude 'node_modules/' \
           -e ssh \
           ./ ${TARGET}:/opt/glance/

ssh ${TARGET} "cd /opt/glance && source venv/bin/activate && python -c 'from db import init_db; init_db(); from app import _seed_images; _seed_images()' && systemctl restart glance"

echo "Deployed and restarted."
