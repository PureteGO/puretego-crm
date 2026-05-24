# Tasks

## 1. Fix Critical 500 Errors (DONE)
- [x] Fix `DetachedInstanceError` across all routes via exhaustive `joinedload`. <!-- id: 0 -->
- [x] Implement safety checks for null values in models and templates. <!-- id: 1 -->
- [x] Resolved missing routes (health_checks.create/delete) causing render failures. <!-- id: 7 -->
- [x] Hardened dashboard/context logic against production data discrepancies.
- [x] Implemented global try-except safety net for dashboard routes.

## 2. Health Check Optimization (DONE)
- [x] Intelligent recommendations generation in Spanish. <!-- id: 8 -->
- [x] Automated detection of top critical issues from SerpApi data. <!-- id: 9 -->
- [x] Full CRUD for audits (Create, View, List, Delete). <!-- id: 10 -->

## 3. Localization & Detailed Info (DONE)
- [x] Migrate interface and logic to Spanish (Paraguay). <!-- id: 11 -->
- [x] Implement detailed client fields (Decision maker, contact preferences, etc.). <!-- id: 12 -->

## 4. Dashboard & Agenda (DONE)
- [x] Unified agenda showing both visits and scheduled interactions. <!-- id: 13 -->
- [x] Real-time statistics and status charts. <!-- id: 14 -->
- [x] Display business name prominently on Kanban cards.
- [x] Add double-click shortcut to Kanban cards to open client view.

## 7. Infrastructure & Stability (DONE - 2026-05-11)
- [x] Resolved production 500 errors by fixing `DetachedInstanceError` in `services.py` using request-scoped `db_session`.
- [x] Cleaned up `run.py` to remove generic 503 error masking, allowing for transparent debugging.
- [x] Reconfigured LiteSpeed VirtualHost aliases to support `app2.maps2go.online` correctly.
- [x] Issued and installed a valid Let's Encrypt SSL certificate for `app2.maps2go.online`.
- [x] Migrated backend runner to a managed Gunicorn systemd service on port 5005 for improved reliability.

## 8. Next Steps: SaaS Commercial Launch (PENDING)
- [ ] Field testing with new prospects (Tomorrow).
- [ ] Final UI/UX adaptations based on field feedback.
- [ ] Prepare for official SaaS sales launch.

## 5. Brainstorming & Design (IN PROGRESS)
- [ ] **Step 3: Design Proposals** <!-- id: 4 -->
    - [x] Create `docs/design_interaction_flow.md`.
    - [ ] Review and Approve Design.
- [ ] **Step 4: Finalize Specifications** <!-- id: 5 -->

## 6. Implementation: Visits & Calls Flow (PENDING)
- [ ] Enhance interaction logging based on brainstorming. <!-- id: 6 -->

## 9. GMB Insights & Reporting (DONE)
- [x] Implement GMB Performance API connectivity check.
- [x] Create Insights Dashboard (Chart.js) in `manage_location.html`.
- [x] Implement Insight synchronization and local caching.
- [x] Design and implement PDF Performance Reports for clients.

