# Execution PM - Date Control & Consistency Guide

This document outlines the business rules, constraints, and automated logic governing dates across the Execution PM system. The goal is to ensure chronological integrity from planning through execution to final project closure.

---

## 🏗️ Phase 1: Planning Controls (`executionpm_planning`)

The planning phase establishes the "temporal bucket" for the project. The system enforces a strict hierarchy: **Project > Lot > Task**.

### 1. Lot Date Boundaries
*   **Rule**: A Lot's start date must be before its end date.
*   **Rule**: A Lot must sit within the project's planned start and end dates.
*   **Constraint**: If a Lot's dates are modified, the system prevents any change that would exclude existing child tasks from the new range.

### 2. Task Date Boundaries
*   **Rule**: A Task's start date must be before its end date.
*   **Rule**: A Task must sit within the overall project timeline.
*   **Rule**: A Task **must** sit within the dates of its parent Lot.
*   **Feedback**: Any deviation triggers an immediate `ValidationError` blocking the save.

---

## 🚧 Phase 2: Execution Controls (`executionpm_execution`)

Execution progress declarations are the primary source of evidence for project advancement.

### 1. Declaration Integrity
*   **No Future Work**: The `Execution Date` cannot be in the future (relative to system date).
*   **Planning Alignment**: The work date must be within the Task's planned start/end dates and the Project's overall start date.

### 2. Progress vs. Time Logic
*   **Premature Completion Block**: The system forbids declaring **100% progress** if the execution date is still before the task's planned end date. This prevents "instant completion" without proper duration.
*   **Delay Detection**: If a progress declaration date is after the planned end date, the system:
    *   Automatically flags the Task and Declaration as **Delayed**.
    *   Computes `delay_days` (Actual Date - Planned End Date).
    *   Displays a warning alert on the record.

---

## ✅ Phase 3: Validation Controls (`executionpm_validation`)

Validation formalizes the declaration and makes the progress "official" for KPI computation.

### 1. Chronological Audit Trail
*   **Validation Sequence**: The Validation Date must be greater than or equal to the Execution Declaration Date.
*   **No Future Validation**: Validators cannot pre-date or post-date a validation decision.
*   **Project Context**: Validation cannot occur before the project's planned start date.

### 2. Automation & Immutability
*   **Auto-Timestamp**: The `validated_date` is automatically set by the system at the moment of validation.
*   **Edit Lock**: Once a validation record is created, the Validation Date is **read-only** and immutable to prevent audit tampering.

---

## 📊 Phase 4: Project Global Consistency

The system automatically derives the Project's actual timeline from validated field data.

### 1. Automatic Milestones
*   **Actual Start Date**: Automatically set at the moment of the **first validated progress declaration**. It is computed as the `min(execution_date)` of all validated records.
*   **Actual End Date**: Automatically set when the project reaches **100% progress**. It is computed as the `max(execution_date)` of all validated records.

### 2. Closure Guardrails
The system blocks the transition to the **"Closed"** state unless:
*   **Completeness**: Overall physical progress is exactly 100%.
*   **Clean Audit**: There are zero (0) pending validations (everything submitted must be either Validated or Rejected).

---

## ⏰ Phase 5: Automated Monitoring (`executionpm_alerts`)

A suite of daily Cron Jobs monitors the system for date-based anomalies and notifies the PMO.

| Alert Name | Condition | Logic |
| :--- | :--- | :--- |
| **Task Not Started** | Progress == 0% | `Today > Planned Start + X Days` |
| **Task Overdue** | Progress < 100% | `Today > Planned End Date` |
| **Inactivity** | No updates | `Last Declaration Date < Today - X Days` |

*   **Notifications**: Automated emails are sent to the Project Manager and Contractor when these thresholds are crossed.
*   **Severity**: Alerts are classified (Low, Medium, High, Critical) based on the magnitude of the date deviation.

---

### Summary Table of Enforcement

| Phase | Field | logic | Enforcement |
| :--- | :--- | :--- | :--- |
| Planning | Lot/Task Dates | Must be inside parent boundaries | `ValidationError` |
| Execution | Declaration Date | Must be <= Today AND >= Planning | `ValidationError` |
| Validation | Validation Date | Must be >= Execution Date | `UserError` |
| Closure | State | Progress < 100% OR Pending > 0 | `Blocking Action` |
| Monitoring | Alert Date | Deviation from plan | `Cron / Notification` |
