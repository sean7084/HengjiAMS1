# Deployment Guide - HengJi AMS

This guide covers deploying HengJi AMS to production environments.

---

## Prerequisites

- **Server**: Linux (Ubuntu 20.04+ recommended) or compatible cloud instance
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **CPU**: 2+ cores
- **Storage**: 20GB+ SSD space
- **Python**: 3.11+
- **PostgreSQL**: 14+
- **Web Server**: Nginx
- **Reverse Proxy**: Gunicorn

---

## Environment Options

### Option 1: Manual Installation

Best for custom deployments, learning, or small-scale deployments.

### Option 2: Docker Containerization (Recommended)

Ideal for consistency, CI/CD integration, and easier scaling.

See [`docker/README.md`](../docker/README.md) for container-specific instructions.

---

## Option 1: Manual Installation Steps

### Step 1: System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    postgresql-14 postgresql-contrib-14 \
    nginx redis-server \
    git curl wget build-essential libpq-dev

# Create system user for application
sudo adduser --system --no-create-home hengjiams
```

### Step 2: PostgreSQL Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE hengjiams_db;
CREATE USER hengjiams_django WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE hengjiams_db TO hengjiams_django;
ALTER DATABASE hengjiams_db OWNER TO hengjiams_django;
\q
```

### Step 3: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/your-org/hengji-ams.git
sudo chown -R hengjiams:hengjiams /opt/hengji-ams
cd /opt/hengji-ams

# Install Python dependencies
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create `.env` file:

```bash
cat > /opt/hengji-ams/.env << EOF
DJANGO_SETTINGS_MODULE=hengjiams.settings
SECRET_KEY=${RANDOM_SECRET_KEY_GENERATED_HERE}
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_NAME=hengjiams_db
DATABASE_USER=hengjiams_django
DATABASE_PASSWORD=your_secure_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
MINIMAX_TOKEN_PLAN_KEY=${YOUR_MINIMAX_API_KEY}
MINIMAX_RFQ_API_URL=https://api.minimax.io/v1/messages
MINIMAX_RFQ_MODEL=MiniMax-M2.7-highspeed
MINIMAX_RFQ_TIMEOUT_SECONDS=30
WEASYPRINT_DLL_DIRECTORIES=/usr/lib/pango/1.0
EOF
```

Generate secret key:
```bash
python3.11 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 5: Run Migrations

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts for username, email, and password
```

### Step 7: Configure Gunicorn

Create systemd service file:

```bash
sudo nano /etc/systemd/system/hengjiams.service
```

Add content:

```ini
[Unit]
Description=HengJi AMS Gunicorn daemon
After=network.target postgresql.service

[Service]
User=hengjiams
Group=hengjiams
WorkingDirectory=/opt/hengji-ams
ExecStart=/opt/hengji-ams/.venv/bin/gunicorn \
    --access-logfile - \
    --error-logfile /var/log/hengjiams/gunicorn-error.log \
    --capture-output \
    --timeout 120 \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    hengjiams.wsgi:application

Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hengjiams
sudo systemctl start hengjiams
sudo systemctl status hengjiams
```

### Step 8: Configure Nginx

Create Nginx config:

```bash
sudo nano /etc/nginx/sites-available/hengjiams
```

Add content:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Static files
    location /static/ {
        alias /opt/hengji-ams/staticfiles/;
        expires 30d;
    }
    
    # Media files
    location /media/ {
        alias /opt/hengji-ams/media/;
        expires 30d;
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
}

# Redirect HTTP to HTTPS (if SSL enabled)
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
    
    # ... same location block as above ...
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/hengjiams /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Auto-renewal test:

```bash
sudo certbot renew --dry-run
```

### Step 10: Background Mail Sync Scheduler

Add to crontab (`crontab -e`):

```cron
# Mailbox sync every 5 minutes during business hours
*/5 8-18 * * 1-5 cd /opt/hengji-ams && source .venv/bin/activate && python manage.py run_mailbox_sync --single-run >> /var/log/hengjiams/mail-sync.log 2>&1
```

Or use Redis/Celery for more robust background task handling.

---

## Option 2: Docker Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Quick Start

```bash
cd /path/to/hengji-ams/docker

# Build images
docker-compose build

# Generate secrets
./scripts/generate-secrets.sh

# Start containers
docker-compose up -d

# Run migrations
docker-compose exec hengjiams python manage.py migrate
docker-compose exec hengjiams python manage.py collectstatic --noinput
docker-compose exec hengjiams python manage.py createsuperuser
```

See `docker/README.md` for detailed configuration.

---

## Production Configuration Checklist

### Security

- ✅ Disable DEBUG mode (`DEBUG=False`)
- ✅ Set strong `SECRET_KEY` (use environment variable, NOT in Git)
- ✅ Restrict `ALLOWED_HOSTS` to actual domains
- ✅ Enable HTTPS everywhere
- ✅ Configure CORS properly
- ✅ Use `require_https` in secure settings

### Database

- ✅ PostgreSQL connection pool settings optimized
- ✅ Read replicas for read-heavy loads (optional)
- ✅ Regular backup schedule configured
- ✅ Failover strategy tested

### Email

- ✅ SMTP credentials secured (not in code)
- ✅ SPF/DKIM/DMARC records configured for domain
- ✅ Outbound email override disabled in production

### Monitoring

- ✅ Logs aggregated (ELK stack, CloudWatch, etc.)
- ✅ Application performance monitoring (New Relic, Sentry)
- ✅ Uptime monitoring (Pingdom, UptimeRobot)
- ✅ Alerting configured (email/slack notifications)

### Maintenance

- ✅ Automated backups scheduled
- ✅ Regular software updates planned
- ✅ Disk space monitoring active
- ✅ Log rotation configured

---

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# /opt/scripts/db-backup.sh

BACKUP_DIR="/backups/hengjiams-db"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="hengjiams_db"

mkdir -p "$BACKUP_DIR"
pg_dump -U hengjiams_django "$DB_NAME" > "$BACKUP_DIR/$DB_NAME_$DATE.sql.gz"
gzip -9 "$BACKUP_DIR/$DB_NAME_$DATE.sql"

# Keep last 30 days
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

Add to cron: `0 2 * * * /opt/scripts/db-backup.sh`

### File Backups

```bash
# Backup static/media files
tar czf "/backups/hengjiams-files_$DATE.tar.gz" \
    /opt/hengji-ams/staticfiles \
    /opt/hengji-ams/media
```

---

## Troubleshooting

### WeasyPrint Issues on Production

**Symptom**: `Missing native GTK/Pango libraries` error

**Solution**:

```bash
# Ubuntu
sudo apt install -y \
    librsvg2-common libpangoft-2-0 libgtk-3-0 \
    libgdk-pixbuf2.0 libffi-dev shared-mime-info

# Verify installation
python3.11 -c "import weasyprint; weasyprint.HTML(string='<div>Hello</div>').write_pdf('-')"
```

### Database Connection Pool Exhaustion

**Symptom**: `too many connections for role hengjiams_django`

**Solution**: Adjust PostgreSQL settings:

```sql
-- Check current connection limit
SELECT datname, numbackends, maxconn FROM pg_database WHERE datname='hengjiams_db';

-- Increase limit (restart PostgreSQL required)
# postgresql.conf
max_connections = 200
```

### Memory Issues

**Symptom**: OOM kills or slow performance

**Mitigations**:
1. Reduce Gunicorn workers: `--workers 2`
2. Increase swap space
3. Optimize database queries (check slow query logs)

---

## Performance Optimization

### Django Settings Adjustments

```python
# Caching (Redis)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Compression middleware
MIDDLEWARE += [
    'django.middleware.gzip.GZipMiddleware',
]

# Static file serving optimization
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Query Optimization Tips

1. Use `select_related()` for ForeignKey relations
2. Use `prefetch_related()` for ManyToMany relations
3. Paginate large datasets
4. Avoid N+1 queries (use `explain()` to detect)
5. Add proper database indexes on frequently queried fields

---

## Updates and Upgrades

### Applying Hotfixes

```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart hengjiams
```

### Major Version Upgrade

See CHANGELOG.md for migration notes per version.

---

## Support & Contact

**Technical Support**: support@hengji.com  
**Emergency Escalation**: +86 XXX-XXXX-XXXX  
**Documentation**: https://docs.hengji.com  

---

*Last Updated: August 20, 2026*
