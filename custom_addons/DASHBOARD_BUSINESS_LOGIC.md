# Dashboard Business Logic Definitions

## Overview

This document defines the **business meaning and domain logic** for all dashboard boxes in the ExecutionPM system. Each dashboard box has been carefully designed to show **only the records that match its business definition**.

> **CRITICAL**: The dashboard data must be 100% accurate for executive decision-making. Zero ambiguity is allowed.

---

## PMO Dashboard Boxes

### 1. Works Waiting Validation

**Business Definition:**
- Progress declarations submitted by contractors
- Currently pending review or being reviewed by PMO/Control Office
- NOT YET validated by PMO

**Domain Logic:**
```python
[
    ('state', 'in', ['submitted', 'under_review']),
    ('state', 'not in', ['validated', 'rejected', 'draft'])
]
```

| Status | Included? | Reason |
|--------|-----------|--------|
| `submitted` | ✅ YES | Freshly submitted, awaiting review |
| `under_review` | ✅ YES | PMO is actively reviewing |
| `draft` | ❌ NO | Not yet submitted by contractor |
| `validated` | ❌ NO | Already approved |
| `rejected` | ❌ NO | Already rejected, waiting for contractor correction |

---

### 2. Tasks Past Planning Deadline

**Business Definition:**
- Tasks whose planned end date has passed
- AND actual validated progress is less than 100%
- Only from approved plannings

**Domain Logic:**
```python
[
    ('date_end', '<', today),
    ('progress_status', '!=', 'completed'),
    ('actual_progress', '<', 100),
    ('planning_id.state', '=', 'approved')
]
```

| Condition | Included? | Reason |
|-----------|-----------|--------|
| date_end < today | ✅ YES | Deadline has passed |
| actual_progress >= 100 | ❌ NO | Task is completed |
| progress_status = 'completed' | ❌ NO | Task is completed |
| planning not approved | ❌ NO | Only show from active plannings |

---

### 3. Urgent: Critical Alerts

**Business Definition:**
- Alerts marked as CRITICAL severity
- Still ACTIVE (not resolved or dismissed)
- Require immediate executive attention

**Domain Logic:**
```python
[
    ('severity', '=', '4_critical'),
    ('state', 'in', ['open', 'acknowledged', 'in_progress']),
    ('state', 'not in', ['resolved', 'dismissed'])
]
```

| Status | Included? | Reason |
|--------|-----------|--------|
| `open` | ✅ YES | New alert requiring action |
| `acknowledged` | ✅ YES | Acknowledged but not yet resolved |
| `in_progress` | ✅ YES | Being worked on |
| `resolved` | ❌ NO | Issue fixed, no longer relevant |
| `dismissed` | ❌ NO | False alarm or closed |

---

## Contractor Dashboard Boxes

### 4. Ongoing Work Packages (In Progress)

**Business Definition:**
- Work packages assigned to the current contractor
- Currently within execution period (started but deadline not passed)
- Not yet completed
- Only from approved plannings

**Domain Logic:**
```python
[
    ('lot_id.planning_id.project_id.execution_contractor_id.related_user_id', '=', uid),
    ('progress_status', '!=', 'completed'),
    ('date_start', '<=', today),
    ('date_end', '>=', today),
    ('planning_id.state', '=', 'approved')
]
```

---

### 5. Delayed Work Packages (Overdue)

**Business Definition:**
- Work packages assigned to the current contractor
- Whose planned end date has passed (overdue)
- But not yet completed
- Only from approved plannings

**Domain Logic:**
```python
[
    ('lot_id.planning_id.project_id.execution_contractor_id.related_user_id', '=', uid),
    ('date_end', '<', today),
    ('actual_progress', '<', 100),
    ('progress_status', '!=', 'completed'),
    ('planning_id.state', '=', 'approved')
]
```

---

### 6. Rejected Reports (Need Correction)

**Business Definition:**
- Progress declarations created by the current contractor
- That have been rejected by PMO/Control Office
- Requiring corrections before resubmission

**Domain Logic:**
```python
[
    ('create_uid', '=', uid),
    ('state', '=', 'rejected')
]
```

| Status | Included? | Reason |
|--------|-----------|--------|
| `rejected` | ✅ YES | Needs contractor correction |
| `draft` | ❌ NO | Not yet submitted |
| `submitted` | ❌ NO | Still pending review |
| `under_review` | ❌ NO | Still being reviewed |
| `validated` | ❌ NO | Approved, no action needed |

---

## Authority Dashboard Boxes

### 7. Total Infrastructure Portfolio

**Business Definition:**
- All execution projects in the system
- Portfolio-level visibility for executives

**Domain Logic:**
```python
[('is_execution_project', '=', True)]
```

---

### 8. Critical Risks (Projects At Risk)

**Business Definition:**
- Execution projects flagged as "at risk"
- Require executive attention and intervention

**Domain Logic:**
```python
[
    ('is_execution_project', '=', True),
    ('execution_state', '=', 'at_risk')
]
```

---

## Validation Rules

After implementation, verify:

| Validation Check | Expected Result |
|-----------------|-----------------|
| Validated record in "Waiting Validation" | ❌ NEVER (BUG if present) |
| Completed task in "Past Deadline" | ❌ NEVER (BUG if present) |
| Resolved alert in "Critical Alerts" | ❌ NEVER (BUG if present) |
| Non-approved task in PMO dashboard | ❌ NEVER (BUG if present) |
| Draft declaration in "Waiting Validation" | ❌ NEVER (BUG if present) |

---

## State Reference Tables

### execution.progress States
| State | Business Meaning |
|-------|-----------------|
| `draft` | Created but not submitted |
| `submitted` | Sent for review |
| `under_review` | PMO is reviewing |
| `validated` | Approved by PMO |
| `rejected` | Rejected, needs correction |

### execution.planning.task Progress Status
| Status | Business Meaning |
|--------|-----------------|
| `not_started` | actual_progress = 0 |
| `in_progress` | 0 < actual_progress < 100 |
| `completed` | actual_progress >= 100 |

### execution.alert States
| State | Business Meaning |
|-------|-----------------|
| `open` | New, unaddressed |
| `acknowledged` | Seen, not yet in progress |
| `in_progress` | Being worked on |
| `resolved` | Issue fixed |
| `dismissed` | Closed without action |

### project.project Execution States
| State | Business Meaning |
|-------|-----------------|
| `draft` | Initial creation |
| `planned` | Planning phase |
| `running` | Active execution |
| `at_risk` | Flagged for executive attention |
| `suspended` | Temporarily halted |
| `closed` | Completed |

---

## Last Updated
2026-01-27 by Senior Odoo Architect

## Target Users
- PMO Directors
- Ministers
- Donors / Auditors
- Control Office
