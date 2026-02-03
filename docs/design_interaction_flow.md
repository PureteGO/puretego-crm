# Design: Visits & Calls (Flexible Cadence)

## 1. Core Concept
A "One-Stop" flow for managing customer interactions. The system acts as a smart assistant, suggesting the logical next step based on what just happened, but always giving the user (you) final control.

## 2. Terminology
*   **Interaction**: An event that happened (Past) or is scheduled (Future). Can be a Visit or a Call.
*   **Type**: The category of the interaction (e.g., "Cold Visit", "Closing Call").
*   **Cadence Rule**: The "brain" that says: "After a *Cold Visit*, usually we do a *Follow-up Call* in *2 days*."

## 3. Proposed "Standard" Types (Editable)
These will be the initial defaults seed in the database, but you can add/change them later.

### 📞 Calls
1.  **Exploratory Call**: First contact to verify interest/data.
2.  **Follow-up Call**: Checking in after a visit or proposal.
3.  **Negotiation Call**: Discussing price/terms.
4.  **Closing Call**: Finalizing the deal.

### 📍 Visits
1.  **Cold Visit (Door Knocking)**: First physical presence without appointment.
2.  **Presentation Visit**: Presenting the proposal (PDF).
3.  **Technical Visit**: Gathering requirements/photos (for Health Check).
4.  **Closing Visit**: Signing the contract.

## 4. The "Smart Suggestion" Flow

### Step A: Logging an Interaction
You just finished visiting **"Taller Mecánico Juan"**.
You open the app and click **"Log Visit"**.
*   Select Type: `Cold Visit`
*   Outcome: `Interested` (Optional note: "Liked the SEO pack")

### Step B: The System Suggestion
Upon saving, the system checks the rules.
*   *Rule detected:* `Cold Visit` -> Suggest `Follow-up Call` (+2 days).

**UI Prompt:**
> "Visit saved! 
> **Standard Next Step:** Call Juan on **Thursday (05/02)**?
>
> [ ✅ Schedule Call ]   [ ✏️ Edit Date/Type ]   [ ❌ No Next Step ]"

### Step C: The Agenda (Daily View)
On Thursday, when you open the app, this scheduled call appears in your **"Today's Tasks"** list.

## 5. Data Model (Technical)
*   **`InteractionType`**: `id`, `name`, `icon`, `is_call` (bool).
*   **`Interaction`**: `client_id`, `type_id`, `date`, `status` (Done/Scheduled), `notes`.
*   **`CadenceRule`**: `trigger_type_id` -> `suggested_next_type_id`, `delay_days`.

## 6. Questions for You
1.  Does the list of types cover your usual workflow?
2.  Does the "Pop-up Suggestion" flow sound comfortable, or would it be annoying?
