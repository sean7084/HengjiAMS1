# Deployment Guide - HengJi AMS

This guide covers deploying HengJi AMS to production environments.

---

## Prerequisites

- **Server**: Ubuntu 24.04 LTS (recommended) or a compatible Linux instance
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **CPU**: 2+ cores
- **Storage**: 20GB+ SSD space
- **Python**: 3.11+ (Ubuntu 24.04 ships 3.12; Django 5.2.8 — see `requirements.txt`)
- **Database**: PostgreSQL 14+ (production). SQLite remains the zero-config default for local development.
- **Cache**: Redis 6+ (production, via `django-redis`). Local development falls back to an in-memory cache.
- **Web Server**: Nginx (serves `/static/` and `/media/` directly)
- **WSGI Server**: Gunicorn

> ✅ **Production dependencies are pinned in `requirements.txt`**: `gunicorn`, `psycopg2-binary`, `whitenoise`, `django-redis`, `redis`. `gunicorn` carries a `sys_platform != 'win32'` marker, so a single `pip install -r requirements.txt` works on both Windows (dev) and Ubuntu (prod) — Windows simply skips gunicorn.

---

## Environment Options

### Option 1: Manual Installation

Best for custom deployments, learning, or small-scale deployments. **This is the only currently supported path.**

### Option 2: Docker Containerization (Not Yet Available)

> ⚠️ **No Docker assets exist in this repository yet.** There is no `docker/` directory, `docker-compose.yml`, or `scripts/generate-secrets.sh`. The section below is a **future plan**, not a working procedure. Use Option 1 until containerization is added.

---

## Option 1: Manual Installation Steps

### Step 1: System Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
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
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

The app loads a repo-local **`.env`** file automatically (`hengjiams/runtime_setup.py::load_local_env`, called by `manage.py`, `wsgi.py`, and `asgi.py`). Create it with the variables that `settings.py` **actually reads**:

```bash
cat > /opt/hengji-ams/.env << EOF
DJANGO_SETTINGS_MODULE=hengjiams.settings

# Django core (REQUIRED in production)
DJANGO_SECRET_KEY=${RANDOM_SECRET_KEY_GENERATED_HERE}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (defaults to SQLite if omitted; set these for PostgreSQL)
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=hengjiams_db
DATABASE_USER=hengjiams_django
DATABASE_PASSWORD=your_secure_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Cache (Redis) - production
DJANGO_REDIS_CACHE_URL=redis://127.0.0.1:6379/1

# Minimax RFQ integration (note the LOWERCASE key name)
minimax_token_plan_key=${YOUR_MINIMAX_API_KEY}
MINIMAX_RFQ_API_URL=https://api.minimaxi.com/anthropic/v1/messages
MINIMAX_RFQ_MODEL=MiniMax-M2.7-highspeed
MINIMAX_RFQ_TIMEOUT_SECONDS=30
MINIMAX_RFQ_MAX_TOKENS=800

# Safety override for non-production email testing (leave empty in prod)
TEST_OUTBOUND_EMAIL_OVERRIDE=
EOF
```

> ✅ **Safety guard:** if `DJANGO_DEBUG=False` while `DJANGO_SECRET_KEY` is unset (still the insecure dev fallback), Django raises `ImproperlyConfigured` at startup. This prevents shipping an insecure key.
>
> 📧 **Email:** outbound email is **not** configured via env vars. It is sent through each user's mailbox settings (`accounts.models.UserMailboxSettings`, stored in the database) with a Django email fallback. There is no `EMAIL_HOST`/`EMAIL_PORT`/etc. in `settings.py`.
>
> 🪟 **WeasyPrint:** `WEASYPRINT_DLL_DIRECTORIES` / `MSYS2_ROOT` are **Windows-only** runtime overrides. On Linux, install the native Pango/GTK libraries instead (see Troubleshooting).

Generate secret key:
```bash
python3.12 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 4b: Provision Document Templates (Required)

The `template_files/` directory is **excluded from Git** (`.gitignore`), but document generation **fails without it** — `quotations/services.py`, `deliveries/services.py`, and `invoices/services.py` raise `FileNotFoundError` when these templates are missing:

| Expected file | Used by |
|---------------|---------|
| `template_files/quotation_template.xlsx` | Quotation Excel/PDF generation |
| `template_files/签收单 template.xlsx` | Delivery (sign-off sheet) generation |
| `template_files/invoice information template.xlsx` | Invoice information sheet |

Copy these templates from a secure internal source into `/opt/hengji-ams/template_files/` before first run. They are **not** distributed with the repository.

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
    
    # Static files (from `manage.py collectstatic`). WhiteNoise gives hashed
    # filenames, so they can be cached immutably for a year.
    location /static/ {
        alias /opt/hengji-ams/staticfiles/;
        access_log off;
        expires 1y;
        add_header Cache-Control "public, immutable";
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

### Step 10: Mailbox Sync (In-Process Thread)

Mailbox synchronization runs as an **in-process background thread**, started automatically with the app — there is **no `run_mailbox_sync` management command** and no cron job is required.

- Implementation: `accounts/mailbox_sync.py` (`start_mailbox_sync_thread`, `maybe_auto_sync_mailbox`).
- Cadence: every `SYNC_INTERVAL_SECONDS` (≈5 minutes) while the server process runs.
- Scope: only mailboxes with `is_active = true` **and** `auto_sync_enabled = true` (`accounts.models.UserMailboxSettings`).

> ⚠️ **Gunicorn note:** the auto-sync thread is designed for the single-process `runserver` workflow. Under multi-worker Gunicorn, each worker may start its own thread. For production, drive sync from a **single** dedicated process (e.g., a `cron`/systemd timer invoking a custom management command you add, or a one-worker service) to avoid duplicate syncing.

---

## Option 2: Docker Deployment (PLANNED — NOT IMPLEMENTED)

> ⚠️ **These files do not exist in the repository yet.** The commands below are illustrative of the intended future setup and will fail if run today. Track this as a backlog item; use **Option 1** for real deployments.

### Intended prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+

### Intended quick start (future)

```bash
# Requires a docker/ directory + compose file that do not exist yet
cd /path/to/hengji-ams/docker
docker-compose build
docker-compose up -d
docker-compose exec hengjiams python manage.py migrate
docker-compose exec hengjiams python manage.py collectstatic --noinput
docker-compose exec hengjiams python manage.py createsuperuser
```

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
python3.12 -c "import weasyprint; weasyprint.HTML(string='<div>Hello</div>').write_pdf('-')"
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

### Django Settings Adjustments (already applied)

Redis caching and WhiteNoise static handling are **already wired into `settings.py`** (env-driven) and pinned in `requirements.txt`:

- **Cache** — `CACHES` uses `django_redis.cache.RedisCache` when `DJANGO_REDIS_CACHE_URL` is set; otherwise a local-memory cache (development).
- **Static files** — in production (`DEBUG=False`), `STORAGES["staticfiles"]` uses `whitenoise.storage.CompressedManifestStaticFilesStorage` and the WhiteNoise middleware is enabled automatically. Run `collectstatic` on every deploy so the manifest and pre-compressed variants exist.

Optional extra (off by default):

```python
# Response compression - only if you do NOT already gzip at Nginx.
MIDDLEWARE += ['django.middleware.gzip.GZipMiddleware']
```

> Prefer Nginx `gzip on;` (plus WhiteNoise's pre-compressed `.gz`/`.br`) over compressing inside the Django process.

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

*Last Updated: September 6, 2026*
