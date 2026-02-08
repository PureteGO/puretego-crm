# PureteGO CRM (Maps2GO) - SaaS Roadmap & Implementation Plan

This document outlines the tasks required to evolve the platform into **Maps2GO**: a full-featured SaaS multi-tenant CRM.

## 🏗️ Core Architecture & Definitions

To ensure consistency in development, we follow these definitions:

*   **Maps2GO**: The SaaS Platform (The Product).
*   **SuperAdmin**: Platform-level user (Manages tenants, plans, billing, and impersonation).
*   **Tenant (ex: PureteGO)**: An agency or consultant client using the platform.
*   **Tenant Roles**: Internal users of a tenant:
    *   **Owner/Admin**: Full control over tenant settings (currency, packages, users).
    *   **SDR**: Cold prospecting and lead qualification focus.
    *   **Vendas/Closer**: Closing deals and managing the pipeline.
    *   **Produção/SEO**: Project implementation and Health Check management.
    *   **Financeiro**: Billing, payment tracking, and revenue forecasting.

---

## 🧭 General Directives

1.  **Strict Isolation**: All data must be isolated by `company_id`.
2.  **Multilingual Mandatory**: All UI strings must support PT, ES, EN using `_()`.
3.  **Tier Enforcement**: Features and limits are gated by Solo, Lean, and Agency plans.
4.  **Role-Based UI**: Views and Dashboards are tailored to the specific context of each user role.

---


## Phase 1: Stabilization & Immediate Fixes
Status: **In Progress**

*   [x] **Fix Syntax/Linting**: Address quoting issues in `clients/index.html` (Done).
*   [x] **Fix Kanban Deletion**: Debug and fix the "Eliminar" (delete stage) functionality in `kanban.html`.
*   [x] **Translation Standardization**: Review and ensure consistent English/Spanish/Portuguese translations across the Kanban and Client views.
*   [x] **Fix Financial Module**: Restore missing Finance navigation and fix `DetachedInstanceError` crashes.

## Phase 2: Company Configuration (Currency & Settings)
Status: **Planned**

*   **Objective**: Allow Company Owners to configure their locale and currency.
*   **Tasks**:
    *   [x] Create a dedicated `/settings/company` route.
    *   [x] Implement a UI to select `currency_symbol` (Gs, R$, $, etc.) and store it in the `Company` model.
    *   [ ] Update all front-end value displays to use the company's `currency_symbol` instead of hardcoded strings.
    *   [ ] Add company logo upload and theme selection (presets already in model).

## Phase 3: Role-Based User Experience
Status: **Planned**

*   **Objective**: Tailor the interface for different user roles (SDR, Finance, Sales).
*   **Tasks**:
    *   **Dashboard Customization**: Create specific widgets/views for each role.
    *   **Module Visibility**:
        *   Restict **SDR** access: Remove "Projects" and "Finance" from their view.
        *   **Admin/Financeiro** View: Create a dedicated tracking screen for sales phases (contracts, billing).
    *   **Permissions Enforcement**: Reinforce backend checks using `user.has_permission()` in all routes.

## Phase 4: SaaS Tier & Resource Management
Status: **Planned**

*   **Objective**: Implement usage limits and feature gates based on the subscription plan.
*   **Tasks**:
    *   **User Limits**: Prevent creating more users than defined in `PLAN_DEFAULTS` for the company's tier.
    *   **Module Gating**: Only show/allow access to modules (Projects, Advanced Reports) included in the current plan.
    *   **Usage Tracking**: Implement counters for monthly health checks and keywords.

## Phase 5: Task Management System
Status: **Planned**

*   **Objective**: Integrate a task system tailored for each tenant.
*   **Tasks**:
    *   Create `Task` model with `company_id`, `assigned_to`, and `client_id` associations.
    *   Implement "Common Tasks" templates (e.g., SDR Follow-up, Closer Documentation).
    *   Add a Dashboard "To-Do" list widget for all users.

## Phase 6: Advanced Commissions & Partners (Requested)
Status: **High Priority**

*   **Objective**: Enhanced commission management for complex sales structures.
*   **Tasks**:
    *   **Partner/Freelancer Registry**: Create a model/registry for external beneficiaries who are NOT full system users (e.g., outsourced partners, freelancers).
    *   **Advanced Commission Splits**: Implement logic to allow splitting a single deal's commission among multiple beneficiaries (e.g., 50% Closer, 25% SDR, 25% Partner).
    *   **Manual Commission Entry**: UI to manually add or adjust commission records for closed deals.

---

## Technical Considerations & Core Directives
*   **Multi-Tenancy**: All new tables must include `company_id`.
*   **Mandatory Multilingual Support**: **ALL** changes, bug fixes, and new features must include and support the project's three languages (Portuguese, Spanish, and English) using Flask-Babel `_()`.
*   **Performance**: Ensure queries are optimized with proper indexing on `company_id`.
