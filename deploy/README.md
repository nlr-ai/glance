# GLANCE Deployment

## Option A: Hetzner VPS (recommended)
1. Create CX22 (4GB RAM, €4/month, Ubuntu 22.04)
2. Point DNS: glance.scisense.fr → VPS IP
3. `scp -r deploy/ root@VPS_IP:/tmp/`
4. `ssh root@VPS_IP 'bash /tmp/deploy/setup.sh'`
5. `./deploy/rsync_deploy.sh root@VPS_IP`
6. Enable SSL: `ssh root@VPS_IP 'certbot --nginx -d glance.scisense.fr'`

## Option B: Docker
1. `docker build -t glance .`
2. `docker run -p 8751:8751 glance`

## Requirements
- Python 3.12+
- 4GB RAM (for mpnet-base-v2 model)
- ~2GB disk (model + GA library)
