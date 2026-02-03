# Deployment Instructions (crm.puretego.online)

These instructions outline how to manually deploy the application if the automated agent deployment is not used.

## Prerequisites
- **cPanel Account**: `crm.puretego.online`
- **Shell Access**: Enabled (SSH enabled in WHM/cPanel).
- **Python**: Version 3.11+ installed (via CloudLinux Python Selector).

## Files Required
- `deploy_v2.zip` (Contains all application code and scripts)

## Steps

### 1. Upload
1.  Log in to cPanel File Manager or use FTP/SCP.
2.  Upload `deploy_v2.zip` to the **Project Root** (e.g., `/home/puretego_crm/repositories/puretego-crm` or directly to `public_html` if hosting directly, though outside public_html is recommended).
    *   *Recommendation*: Create a folder `app` outside `public_html`.

### 2. Extract
1.  Unzip the archive:
    ```bash
    unzip deploy_v2.zip
    ```

### 3. Automated Setup
1.  Run the included setup script:
    ```bash
    chmod +x deploy/setup_crm.sh
    ./deploy/setup_crm.sh
    ```
    *   This will create the virtual environment globally for the project, install `requirements_linux.txt`, and create necessary folders.

### 4. Configuration
1.  Rename `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```
2.  Edit `.env` with production keys and database credentials.

### 5. cPanel "Setup Python App"
1.  Go to cPanel -> **Setup Python App**.
2.  **Create Application**:
    *   **Python Version**: 3.11
    *   **App Directory**: Path to where you unzipped (e.g., `app`).
    *   **App Domain**: `crm.puretego.online`
    *   **Startup File**: `passenger_wsgi.py` (Already included in zip).
    *   **Entry Point**: `application`
3.  Click **Create**.

### 6. Verification
1.  Visit `https://crm.puretego.online`
