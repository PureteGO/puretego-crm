# PureteGO CRM - Developer Guidelines (Adopted from Antigravity Skills)

To ensure rapid development without "freezes" (performance issues) and prepare for 5,000+ users, we are adopting the following Engineering Standards.

## 🐍 Python & Performance (from `python-patterns`)

### 1. The Golden Rule of Async
*   **I/O-bound (Database, External APIs)** → Use `async` where possible (Flask 2.0+ supports it, but standard Flask is sync. We use Threading/uWSGI for concurrency currently).
*   **CPU-bound (PDF Generation, Heavy Calc)** → **NEVER** block the main thread. Offload to background workers (Celery) or separate processes.
    *   *Current Risk*: PDF generation is CPU heavy. We must keep it optimized.

### 2. Type Hints Strategy
*   **Always Type**: Function parameters, Return types, Public APIs.
*   **Why**: Catch errors early (IDE support) = Faster coding.

### 3. Error Handling
*   **Never** expose raw stack traces to the frontend (Security Risk).
*   **Always** log errors with context for debugging.

## 🚀 Deployment & Stability (from `deployment-procedures`)

### 1. The 5-Phase Deployment Protocol
1.  **PREPARE**: Local Tests Pass + Build Success.
2.  **BACKUP**: Database dump BEFORE code push.
3.  **DEPLOY**: Execute deployment (GitHub Action).
4.  **VERIFY**: Check Health Endpoint + Error Logs immediately.
5.  **CONFIRM**: If stable, keep. If errors > 1%, **ROLLBACK immediately**.

### 2. Zero-Downtime Goal
*   We aim for "Blue-Green" or "Rolling" updates.
*   On cPanel, this means using atomic folder swaps if possible, or minimizing maintenance windows.

## 🏗️ Architecture for Scale (from `senior-architect`)

### 1. Database-First Design
*   **Schema**: MySQL (Relational). Strict Foreign Keys.
*   **Optimization**: Index all columns used in run-time Filters/Joins.
*   **Migration**: ALL scheme changes must be versioned (using `alembic` or `flask-migrate` in the future).

### 2. Modular Structure
*   `routes/`: API definitions only.
*   `services/`: Business logic.
*   `models/`: Data structure.
*   *Rule*: Routes should never contain complex logic. They just call Services.

---
**Status**: Adopted on 2026-02-02.
