# Production Server Information (cPanel)

**Server:** `app2.maps2go.online` (Zeta)
**Path:** `/home2/app2maps2go/app2.maps2go.online`
**Virtual Environment:** `/home2/app2maps2go/virtualenv/app2.maps2go.online/3.11/bin/activate`
(Note: Python version is **3.11**)

## Common Commands

### 1. Deploy Updates
The code is automatically deployed via GitHub Actions (FTP).
**DO NOT RUN GIT PULL**.

### 2. Install Dependencies
Connect via SSH and run:
```bash
cd /home2/app2maps2go/app2.maps2go.online
source ../virtualenv/app2.maps2go.online/3.11/bin/activate
pip install -r requirements.txt
```

### 3. Restart Application
```bash
touch tmp/restart.txt
```

### 4. Database Migrations (If needed)
```bash
flask db upgrade
# OR
python3 scripts/migrate_db.py
```
