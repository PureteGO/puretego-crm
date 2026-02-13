# Project Rules & Constraints

## Deployment
- **Method**: Automatic via GitHub Actions (FTP).
- **Paths**:
    - App Dir: `~/app2.maps2go.online`
    - Virtualenv: `~/virtualenv/app2.maps2go.online/3.11`
- **Constraint**: NEVER suggest or use `git pull origin main` on the production server. The server files are managed via the GitHub Action deployment flow.
- **Manual Steps**: After the auto-deployment, copy and paste this block:
```bash
cd ~/app2.maps2go.online && source ../virtualenv/app2.maps2go.online/3.11/bin/activate && python3 recompile_translations.py && touch tmp/restart.txt
```

## Internationalization
- **Mandatory Requirement**: ALL changes, implementations, and new features MUST support and be correctly reflected in **Portuguese, Spanish, and English**.
- **Source Language**: English (keys are often used as IDs).
- **Catalogs**: `pt_BR`, `es`, `en`.
- **Compilation**: Must use `recompile_translations.py` (which wraps `pybabel compile`).
