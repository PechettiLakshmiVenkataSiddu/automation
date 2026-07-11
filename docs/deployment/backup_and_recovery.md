# Backup and Recovery Procedures

This runbook guides system administrators through database backup automation, data restoration validation, storage syncs, and disaster recovery procedures.

---

## 1. Database Backups (`pg_dump`)

### Manual Backup Trigger
To execute an immediate backup of the production PostgreSQL database:
```bash
docker exec -t aether-db pg_dump -U postgres -d aether | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Automated Daily Cron Job
Place this backup script in `/etc/cron.daily/aether-backup`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/aether"
DATE=$(date +%Y-%m-%d)
FILENAME="${BACKUP_DIR}/aether_db_${DATE}.sql.gz"

mkdir -p ${BACKUP_DIR}
docker exec -t aether-db pg_dump -U postgres -d aether | gzip > ${FILENAME}

# Retain only the last 30 days of backups
find ${BACKUP_DIR} -type f -mtime +30 -name "*.sql.gz" -delete
```

---

## 2. Restoration & Recovery Verification Drills

To verify backup integrity regularly, perform a test restore into a secondary sandbox environment:

```bash
# 1. Create test database
docker exec -i aether-db psql -U postgres -c "CREATE DATABASE aether_restore_test;"

# 2. Extract and pipe backup SQL into test database
gunzip -c backup_xxxx_xx_xx.sql.gz | docker exec -i aether-db psql -U postgres -d aether_restore_test

# 3. Verify restore completion
docker exec -i aether-db psql -U postgres -d aether_restore_test -c "\dt"
```

---

## 3. Object Storage Data Backup (MinIO)

File attachments and execution artifacts uploaded by tasks are stored in the Object Storage container.
To sync MinIO buckets to a remote backup location (like an external cloud storage bucket):
```bash
# Sync local MinIO data directory
aws s3 sync /var/lib/docker/volumes/automation_miniodata/_data s3://my-aether-backups-bucket/storage/
```

---

## 4. Disaster Recovery (DR) Steps

In the event of a total server VM or hardware failure:

### Step 1: Provision Clean Server Instance
1. Spin up a clean Linux VM (Ubuntu 22.04+ or equivalent).
2. Install Docker, git, and python.

### Step 2: Retrieve Source Code & Backups
1. Clone the project repository:
   ```bash
   git clone https://github.com/your-org/aether.git /opt/aether
   ```
2. Pull the latest DB backup (`.sql.gz`) and Object Storage snapshot from the secure offsite location.

### Step 3: Spin Up Database & Storage Containers
1. Spin up only the DB and Storage services:
   ```bash
   docker compose up -d db storage redis chroma
   ```
2. Wait for the database container to become healthy.

### Step 4: Restore Data
1. Restore database schema and entries:
   ```bash
   gunzip -c aether_db_latest.sql.gz | docker exec -i aether-db psql -U postgres -d aether
   ```
2. Restore MinIO directories into the `automation_miniodata` docker volume mount path.

### Step 5: Start API & Frontend
Start the remaining containers:
```bash
docker compose up -d api worker scheduler web nginx
```
Verify page liveness by visiting `http://localhost/`.
