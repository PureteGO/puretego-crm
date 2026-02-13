# Production Server Information (cPanel)

**Server:** `app2.maps2go.online` (Zeta)
**Path:** `/home2/app2maps2go/app2.maps2go.online`
**Virtual Environment:** `/home2/app2maps2go/virtualenv/app2.maps2go.online/3.11/bin/activate`
(Note: Python version is **3.11**)

## Deployment Protocol (Updated 2026-02-13)

**User Preference:**
- **Code Deployment:** FTP (Manual or GitHub Actions if configured, but Manual preferred for small fixes without git overhead).
- **Database Changes:** Manual SQL execution via **phpMyAdmin**. Avoid automated Python migration scripts unless necessary.

### 1. Database Updates (phpMyAdmin)
For any database schema change (new columns, tables):
1.  Generate the SQL `ALTER TABLE` or `CREATE TABLE` command.
2.  Log in to cPanel -> phpMyAdmin.
3.  Select the database `app2maps2go_crm`.
4.  Run the SQL command in the "SQL" tab.

### 2. Code Updates (FTP)
1.  Upload modified files to `/home2/app2maps2go/app2.maps2go.online` via FileZilla or cPanel File Manager.
2.  **Avoid** uploading `node_modules` or `__pycache__`.

### 3. Restart Application (Required after ANY change)
1.  Connect via SSH or use cPanel Terminal.
2.  Run:
    ```bash
    touch tmp/restart.txt
    ```

### 4. Install Dependencies (Only if `requirements.txt` changed)
1.  Connect via SSH.
2.  Run:
    ```bash
    cd /home2/app2maps2go/app2.maps2go.online
    source ../virtualenv/app2.maps2go.online/3.11/bin/activate
    pip install -r requirements.txt
    ```
