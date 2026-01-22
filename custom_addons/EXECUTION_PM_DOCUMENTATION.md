# Execution PM - Complete System Documentation

**System:** Execution Project Management for Infrastructure Projects  
**Odoo Version:** 18.0  
**Created:** January 20, 2026  
**Last Updated:** January 20, 2026  
**License:** LGPL-3

---

## 📋 System Overview

The **Execution PM** system is a comprehensive solution for managing infrastructure execution projects. It extends Odoo's native Project module to handle the complete lifecycle of public infrastructure works, from planning through execution tracking and progress validation.

---

## 🧩 Module Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXECUTION PM SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────┐                                              │
│  │  executionpm_core │  ◄── Foundation Module                       │
│  │  (Base Module)    │      - Project extensions                    │
│  │                   │      - Lifecycle states                      │
│  │                   │      - Security groups                       │
│  └─────────┬─────────┘                                              │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────────┐                                          │
│  │ executionpm_planning  │  ◄── Planning Module                     │
│  │ (Depends on core)     │      - Detailed scheduling               │
│  │                       │      - Lots & Tasks                      │
│  │                       │      - Approval workflow                 │
│  └─────────┬─────────────┘                                          │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────────┐                                          │
│  │ executionpm_execution │  ◄── Execution Module                    │
│  │ (Depends on planning) │      - Progress declarations             │
│  │                       │      - Proof attachments                 │
│  │                       │      - Basic validation                  │
│  └─────────┬─────────────┘                                          │
│            │                                                        │
│            ▼                                                        │
│  ┌─────────────────────────┐                                        │
│  │ executionpm_validation  │  ◄── Validation Module                 │
│  │ (Depends on execution)  │      - Formal validation authority     │
│  │                         │      - Immutable audit trail           │
│  │                         │      - Correction workflow             │
│  │                         │      - Automatic KPI updates           │
│  └─────────────────────────┘                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# Module 1: executionpm_core

## Purpose
Foundation module that extends `project.project` with infrastructure-specific fields and lifecycle management.

## Key Features
- **National Project Code**: Auto-generated unique identifier (FORMAT: TYPE-SECTOR-YEAR-SEQ)
- **Project Types**: Water, Energy, Transport, Buildings, etc.
- **Geographic Sectors**: Hierarchical administrative regions
- **Funding Sources**: Government, Private, International, etc.
- **Budget Tracking**: Total budget, committed, spent, remaining
- **Lifecycle States**: Draft → Planned → Running → Closed (with At Risk / Suspended exceptions)

## Models Created

| Model | Description |
|-------|-------------|
| `project.project` (Extended) | Added execution-specific fields |
| `execution.project.type` | Project type master data |
| `execution.sector` | Hierarchical geographic sectors |
| `execution.funding.source` | Funding source master data |

## Project Lifecycle States

| State | Description | Entry Requirements |
|-------|-------------|-------------------|
| `draft` | Initial creation | None |
| `planned` | Approved for execution | Budget + Dates required |
| `running` | Active execution | Approved Planning required |
| `at_risk` | Flagged for attention | Manual flag + reason |
| `suspended` | Work stopped | Manual + reason |
| `closed` | Completed | Progress = 100% |

## Security Groups

| Group | Permissions |
|-------|-------------|
| Execution User | Basic access |
| Execution Validator | Review & validate progress |
| Execution Manager | Full project management |
| Execution Administrator | System configuration |

---

# Module 2: executionpm_planning

## Purpose
Manages detailed execution planning submitted by contractors. Enforces approval before project execution can begin.

## Key Features
- **Structured Planning**: Project → Lots → Tasks hierarchy
- **Physical Weighting**: Each task has a weight contribution (Total must = 100%)
- **Approval Workflow**: Draft → Submitted → Approved/Rejected
- **Execution Gate**: Project cannot start without approved planning

## Models Created

| Model | Description |
|-------|-------------|
| `execution.planning` | Master planning document |
| `execution.planning.lot` | Work packages / lots |
| `execution.planning.task` | Granular tasks with dates & weights |

## Planning Structure

```
execution.planning (Document)
│
├── execution.planning.lot (Work Package 1)
│   ├── execution.planning.task (Task 1.1) - 15% weight
│   ├── execution.planning.task (Task 1.2) - 10% weight
│   └── execution.planning.task (Task 1.3) - 5% weight
│
├── execution.planning.lot (Work Package 2)
│   ├── execution.planning.task (Task 2.1) - 25% weight
│   └── execution.planning.task (Task 2.2) - 20% weight
│
└── execution.planning.lot (Work Package 3)
    └── execution.planning.task (Task 3.1) - 25% weight
                                            ───────────
                                    TOTAL = 100% ✓
```

## Planning Workflow

```
┌───────┐    ┌───────────┐    ┌──────────┐
│ Draft │───▶│ Submitted │───▶│ Approved │
└───────┘    └─────┬─────┘    └──────────┘
                   │
                   ▼
             ┌──────────┐
             │ Rejected │
             └──────────┘
```

## Business Rules
1. **Weight Validation**: Total task weights must equal exactly 100%
2. **Execution Gate**: Project cannot transition to "Running" without an approved planning
3. **Edit Control**: Only contractors can edit planning in Draft state
4. **Approval Authority**: Only PMO/Managers can approve or reject

---

# Module 3: executionpm_execution

## Purpose
Enables contractors to declare execution progress per task with mandatory proof. Validated progress updates project KPIs.

## Key Features
- **Task-Level Progress**: Declarations linked to planning tasks
- **Incremental Tracking**: Auto-calculates progress increment
- **Mandatory Proof**: Attachments required before submission
- **Multi-Step Validation**: Draft → Submitted → Under Review → Validated/Rejected
- **KPI Protection**: Only validated progress impacts project metrics

## Models Created

| Model | Description |
|-------|-------------|
| `execution.progress` | Progress declaration |
| `execution.planning.task` (Extended) | Added actual_progress field |

## Progress Declaration Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | Many2one | Linked planning task |
| `declared_percentage` | Float | Cumulative progress (0-100%) |
| `previous_percentage` | Float | Last validated % (computed) |
| `incremental_percentage` | Float | Progress increment (computed) |
| `quantity_executed` | Float | Physical quantity done |
| `execution_date` | Date | Date of work |
| `comment` | Text | Description (required) |
| `attachment_ids` | Many2many | Proof documents (required) |

## Progress Workflow

```
┌───────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
│ Draft │───▶│ Submitted │───▶│ Under Review │───▶│ Validated │
└───────┘    └─────┬─────┘    └──────┬───────┘    └───────────┘
                   │                 │
                   ▼                 ▼
             ┌──────────┐     ┌──────────┐
             │ Rejected │◄────│ Rejected │
             └──────────┘     └──────────┘
```

## Business Rules
1. **Mandatory Attachments**: Cannot submit without proof documents
2. **Progressive Only**: Declared % cannot be less than previous validated %
3. **KPI Update**: Task's `actual_progress` updates ONLY on validation
4. **Edit Lock**: Validated declarations cannot be modified
5. **Own Declarations**: Users can only edit their own draft/rejected records

---

# Module 4: executionpm_validation

## Purpose
Formalizes the validation process with immutable audit trails, separating validation authority from declaration authority. All validation decisions are timestamped, hashed for integrity, and cannot be modified after creation.

## Key Features
- **Immutable Validation Records**: Cannot be modified or deleted after creation
- **Correction Workflow**: Request corrections with mandatory comments
- **Integrity Hash**: SHA-256 hash for audit verification
- **Automatic KPI Updates**: Project progress calculated on validation
- **Separation of Authority**: Validators cannot validate their own declarations

## Models Created

| Model | Description |
|-------|-------------|
| `execution.validation` | Immutable validation record |
| `execution.progress` (Extended) | Added correction workflow |
| `execution.planning.task` (Extended) | Validation statistics |
| `project.project` (Extended) | Pending validation counts |

## Validation Record Fields

| Field | Type | Description |
|-------|------|-------------|
| `progress_id` | Many2one | Linked progress declaration |
| `decision` | Selection | `validated` / `rejected` / `correction_requested` |
| `validation_datetime` | Datetime | Timestamp (immutable) |
| `validator_id` | Many2one | Who validated |
| `validator_role` | Char | Role at validation time |
| `comment` | Text | Mandatory for rejection/correction |
| `declared_percentage_snapshot` | Float | Progress % at validation time |
| `validation_hash` | Char | SHA-256 integrity hash |

## Extended Workflow (with Correction)

```
┌───────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
│ Draft │───▶│ Submitted │───▶│ Under Review │───▶│ Validated │
└───────┘    └─────┬─────┘    └──────┬───────┘    └───────────┘
                   │                 │
                   │                 ├───▶ Rejected
                   │                 │
                   └─────────────────┴───▶ Correction Requested
                                                     │
                                                     ▼
                                              (Contractor fixes)
                                                     │
                                                     ▼
                                              ┌────────────┐
                                              │ Resubmit   │
                                              └────────────┘
```

## Immutability Features
- ❌ Cannot be modified after creation (raises UserError)
- ❌ Cannot be deleted (raises UserError)
- ✅ Integrity hash generated on creation
- ✅ Snapshot of progress values preserved
- ✅ Validator role captured at decision time

## Validation Authority Rules

| Authority | Can Declare | Can Validate | Can Reject | Can Request Correction |
|-----------|-------------|--------------|------------|------------------------|
| **User** (Contractor) | ✅ | ❌ | ❌ | ❌ |
| **Validator** (PMO) | ❌ | ✅ | ✅ | ✅ |
| **Manager** | ✅ | ✅ | ✅ | ✅ |

## Business Rules
1. **Separation of Authority**: Validators cannot validate their own declarations
2. **Mandatory Comments**: Rejection and correction require meaningful comments (10+ chars)
3. **Immutable Records**: Validation decisions cannot be changed
4. **Audit Trail**: All decisions are permanently recorded
5. **KPI Calculation**: Project progress = weighted average of validated task progress

---

# 🔄 Complete Business Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROJECT LIFECYCLE FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CREATE PROJECT (executionpm_core)                               │
│     └── Set type, sector, budget, dates                             │
│         └── State: DRAFT                                            │
│                                                                     │
│  2. PLAN PROJECT (executionpm_core)                                 │
│     └── Set budget + planned dates                                  │
│         └── State: PLANNED                                          │
│                                                                     │
│  3. CREATE PLANNING (executionpm_planning)                          │
│     └── Contractor creates lots & tasks                             │
│     └── Assigns weights (must = 100%)                               │
│     └── Submits for approval                                        │
│         └── Planning State: SUBMITTED → APPROVED                    │
│                                                                     │
│  4. START EXECUTION (executionpm_core)                              │
│     └── System checks: Has approved planning?                       │
│         └── If YES: State: RUNNING                                  │
│         └── If NO: ERROR - Cannot start                             │
│                                                                     │
│  5. DECLARE PROGRESS (executionpm_execution)                        │
│     └── Contractor creates progress declaration                     │
│     └── Attaches proof documents                                    │
│     └── Submits for validation                                      │
│         └── Progress State: SUBMITTED → UNDER_REVIEW                │
│                                                                     │
│  6. VALIDATE PROGRESS (executionpm_validation)                      │
│     └── Validator (PMO) reviews declaration                         │
│     └── Three options:                                              │
│         ├── VALIDATE: Creates immutable record, updates KPIs        │
│         ├── REJECT: Requires comment, contractor can restart        │
│         └── REQUEST CORRECTION: Requires comment, contractor fixes  │
│                                                                     │
│  7. CORRECTION CYCLE (if needed)                                    │
│     └── Contractor receives correction comments                     │
│     └── Makes required corrections                                  │
│     └── Resubmits for validation                                    │
│                                                                     │
│  8. COMPLETE PROJECT (executionpm_core)                             │
│     └── When all tasks at 100%                                      │
│     └── Project progress = 100%                                     │
│         └── State: CLOSED                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 📁 Complete File Structure

```
custom_addons/
│
├── EXECUTION_PM_DOCUMENTATION.md    ◄── This file
├── USER_MANAGEMENT_GUIDE.md        ◄── Guide des Rôles et Utilisateurs
│
├── executionpm_core/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── SUMMARY.md
│   ├── data/
│   │   ├── execution_project_type_data.xml
│   │   ├── execution_sector_data.xml
│   │   └── ir_sequence_data.xml
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution_project.py
│   │   ├── execution_project_type.py
│   │   ├── execution_sector.py
│   │   └── execution_funding_source.py
│   ├── security/
│   │   ├── executionpm_security.xml
│   │   └── ir.model.access.csv
│   ├── static/description/
│   │   └── icon.svg
│   └── views/
│       ├── execution_project_views.xml
│       ├── execution_project_type_views.xml
│       ├── execution_sector_views.xml
│       ├── execution_funding_source_views.xml
│       └── menu_views.xml
│
├── executionpm_planning/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── SUMMARY.md
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution_planning.py
│   │   ├── execution_planning_lot.py
│   │   ├── execution_planning_task.py
│   │   └── project_project.py
│   ├── security/
│   │   ├── executionpm_planning_security.xml
│   │   └── ir.model.access.csv
│   └── views/
│       ├── execution_planning_views.xml
│       ├── execution_planning_lot_views.xml
│       ├── execution_planning_task_views.xml
│       ├── project_project_views.xml
│       └── menu_views.xml
│
├── executionpm_execution/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── SUMMARY.md
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution_progress.py
│   │   └── execution_planning_task.py
│   ├── security/
│   │   ├── executionpm_execution_security.xml
│   │   └── ir.model.access.csv
│   └── views/
│       ├── execution_progress_views.xml
│       ├── execution_planning_task_views.xml
│       └── menu_views.xml
│
└── executionpm_validation/
    ├── __init__.py
    ├── __manifest__.py
    ├── SUMMARY.md
    ├── models/
    │   ├── __init__.py
    │   ├── execution_validation.py
    │   ├── execution_progress.py
    │   ├── execution_planning_task.py
    │   └── project_project.py
    ├── wizards/
    │   ├── __init__.py
    │   ├── validation_wizard.py
    │   └── validation_wizard_views.xml
    ├── security/
    │   ├── executionpm_validation_security.xml
    │   └── ir.model.access.csv
    └── views/
        ├── execution_validation_views.xml
        ├── execution_progress_views.xml
        └── menu_views.xml
```

---

# 🚀 Installation Order

Install modules in this order (dependencies are handled automatically):

1. `executionpm_core` - Base module
2. `executionpm_planning` - Depends on core
3. `executionpm_execution` - Depends on planning
4. `executionpm_validation` - Depends on execution

**Command:**
```bash
./odoo-bin -c odoo.conf -i executionpm_core,executionpm_planning,executionpm_execution,executionpm_validation -d your_database
```

---

# 🔐 Security Summary

| Group | Core | Planning | Execution | Validation |
|-------|------|----------|-----------|------------|
| User | View projects, basic edits | Create/edit own planning (draft) | Create/edit own declarations | View audit trail |
| Validator | - | - | Review declarations | Validate/Reject/Request Correction |
| Manager | Full project control | Approve/reject planning | Full declaration control | Full validation control |
| Administrator | System config | - | - | - |

---

# 📊 Menu Structure

```
Execution PM (Main App)
│
├── Projects
│   ├── All Projects
│   └── Project Dashboard
│
├── Planning
│   └── Execution Plans
│
├── Execution
│   ├── To Review
│   └── All Declarations
│
├── Validation
│   └── Audit Trail
│
└── Configuration
    ├── Project Types
    ├── Sectors
    └── Funding Sources
```

---

*Execution PM System v18.0.1.0.0 - Complete Documentation (4 Modules)*


## 📋 System Overview

The **Execution PM** system is a comprehensive solution for managing infrastructure execution projects. It extends Odoo's native Project module to handle the complete lifecycle of public infrastructure works, from planning through execution tracking and progress validation.

---

## 🧩 Module Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EXECUTION PM SYSTEM                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────┐                                              │
│  │  executionpm_core │  ◄── Foundation Module                       │
│  │  (Base Module)    │      - Project extensions                    │
│  │                   │      - Lifecycle states                      │
│  │                   │      - Security groups                       │
│  └─────────┬─────────┘                                              │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────────┐                                          │
│  │ executionpm_planning  │  ◄── Planning Module                     │
│  │ (Depends on core)     │      - Detailed scheduling               │
│  │                       │      - Lots & Tasks                      │
│  │                       │      - Approval workflow                 │
│  └─────────┬─────────────┘                                          │
│            │                                                        │
│            ▼                                                        │
│  ┌───────────────────────┐                                          │
│  │ executionpm_execution │  ◄── Execution Module                    │
│  │ (Depends on planning) │      - Progress declarations             │
│  │                       │      - Proof attachments                 │
│  │                       │      - Validation workflow               │
│  └───────────────────────┘                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# Module 1: executionpm_core

## Purpose
Foundation module that extends `project.project` with infrastructure-specific fields and lifecycle management.

## Key Features
- **National Project Code**: Auto-generated unique identifier (FORMAT: TYPE-SECTOR-YEAR-SEQ)
- **Project Types**: Water, Energy, Transport, Buildings, etc.
- **Geographic Sectors**: Hierarchical administrative regions
- **Funding Sources**: Government, Private, International, etc.
- **Budget Tracking**: Total budget, committed, spent, remaining
- **Lifecycle States**: Draft → Planned → Running → Closed (with At Risk / Suspended exceptions)

## Models Created

| Model | Description |
|-------|-------------|
| `project.project` (Extended) | Added execution-specific fields |
| `execution.project.type` | Project type master data |
| `execution.sector` | Hierarchical geographic sectors |
| `execution.funding.source` | Funding source master data |

## Project Lifecycle States

| State | Description | Entry Requirements |
|-------|-------------|-------------------|
| `draft` | Initial creation | None |
| `planned` | Approved for execution | Budget + Dates required |
| `running` | Active execution | Approved Planning required |
| `at_risk` | Flagged for attention | Manual flag + reason |
| `suspended` | Work stopped | Manual + reason |
| `closed` | Completed | Progress = 100% |

## Security Groups

| Group | Permissions |
|-------|-------------|
| Execution User | Basic access |
| Execution Validator | Review & validate progress |
| Execution Manager | Full project management |
| Execution Administrator | System configuration |

---

# Module 2: executionpm_planning

## Purpose
Manages detailed execution planning submitted by contractors. Enforces approval before project execution can begin.

## Key Features
- **Structured Planning**: Project → Lots → Tasks hierarchy
- **Physical Weighting**: Each task has a weight contribution (Total must = 100%)
- **Approval Workflow**: Draft → Submitted → Approved/Rejected
- **Execution Gate**: Project cannot start without approved planning

## Models Created

| Model | Description |
|-------|-------------|
| `execution.planning` | Master planning document |
| `execution.planning.lot` | Work packages / lots |
| `execution.planning.task` | Granular tasks with dates & weights |

## Planning Structure

```
execution.planning (Document)
│
├── execution.planning.lot (Work Package 1)
│   ├── execution.planning.task (Task 1.1) - 15% weight
│   ├── execution.planning.task (Task 1.2) - 10% weight
│   └── execution.planning.task (Task 1.3) - 5% weight
│
├── execution.planning.lot (Work Package 2)
│   ├── execution.planning.task (Task 2.1) - 25% weight
│   └── execution.planning.task (Task 2.2) - 20% weight
│
└── execution.planning.lot (Work Package 3)
    └── execution.planning.task (Task 3.1) - 25% weight
                                            ───────────
                                    TOTAL = 100% ✓
```

## Planning Workflow

```
┌───────┐    ┌───────────┐    ┌──────────┐
│ Draft │───▶│ Submitted │───▶│ Approved │
└───────┘    └─────┬─────┘    └──────────┘
                   │
                   ▼
             ┌──────────┐
             │ Rejected │
             └──────────┘
```

## Business Rules
1. **Weight Validation**: Total task weights must equal exactly 100%
2. **Execution Gate**: Project cannot transition to "Running" without an approved planning
3. **Edit Control**: Only contractors can edit planning in Draft state
4. **Approval Authority**: Only PMO/Managers can approve or reject

---

# Module 3: executionpm_execution

## Purpose
Enables contractors to declare execution progress per task with mandatory proof. Validated progress updates project KPIs.

## Key Features
- **Task-Level Progress**: Declarations linked to planning tasks
- **Incremental Tracking**: Auto-calculates progress increment
- **Mandatory Proof**: Attachments required before submission
- **Multi-Step Validation**: Draft → Submitted → Under Review → Validated/Rejected
- **KPI Protection**: Only validated progress impacts project metrics

## Models Created

| Model | Description |
|-------|-------------|
| `execution.progress` | Progress declaration |
| `execution.planning.task` (Extended) | Added actual_progress field |

## Progress Declaration Fields

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | Many2one | Linked planning task |
| `declared_percentage` | Float | Cumulative progress (0-100%) |
| `previous_percentage` | Float | Last validated % (computed) |
| `incremental_percentage` | Float | Progress increment (computed) |
| `quantity_executed` | Float | Physical quantity done |
| `execution_date` | Date | Date of work |
| `comment` | Text | Description (required) |
| `attachment_ids` | Many2many | Proof documents (required) |

## Progress Workflow

```
┌───────┐    ┌───────────┐    ┌──────────────┐    ┌───────────┐
│ Draft │───▶│ Submitted │───▶│ Under Review │───▶│ Validated │
└───────┘    └─────┬─────┘    └──────┬───────┘    └───────────┘
                   │                 │
                   ▼                 ▼
             ┌──────────┐     ┌──────────┐
             │ Rejected │◄────│ Rejected │
             └──────────┘     └──────────┘
```

## Business Rules
1. **Mandatory Attachments**: Cannot submit without proof documents
2. **Progressive Only**: Declared % cannot be less than previous validated %
3. **KPI Update**: Task's `actual_progress` updates ONLY on validation
4. **Edit Lock**: Validated declarations cannot be modified
5. **Own Declarations**: Users can only edit their own draft/rejected records

---

# 🔄 Complete Business Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROJECT LIFECYCLE FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. CREATE PROJECT (executionpm_core)                               │
│     └── Set type, sector, budget, dates                             │
│         └── State: DRAFT                                            │
│                                                                     │
│  2. PLAN PROJECT (executionpm_core)                                 │
│     └── Set budget + planned dates                                  │
│         └── State: PLANNED                                          │
│                                                                     │
│  3. CREATE PLANNING (executionpm_planning)                          │
│     └── Contractor creates lots & tasks                             │
│     └── Assigns weights (must = 100%)                               │
│     └── Submits for approval                                        │
│         └── Planning State: SUBMITTED → APPROVED                    │
│                                                                     │
│  4. START EXECUTION (executionpm_core)                              │
│     └── System checks: Has approved planning?                       │
│         └── If YES: State: RUNNING                                  │
│         └── If NO: ERROR - Cannot start                             │
│                                                                     │
│  5. DECLARE PROGRESS (executionpm_execution)                        │
│     └── Contractor creates progress declaration                     │
│     └── Attaches proof documents                                    │
│     └── Submits for validation                                      │
│         └── Progress State: SUBMITTED → UNDER_REVIEW                │
│                                                                     │
│  6. VALIDATE PROGRESS (executionpm_execution)                       │
│     └── Validator reviews declaration                               │
│     └── Approves or rejects                                         │
│         └── On VALIDATE: Task actual_progress updated               │
│         └── On REJECT: Contractor corrects and resubmits            │
│                                                                     │
│  7. COMPLETE PROJECT (executionpm_core)                             │
│     └── When all tasks at 100%                                      │
│     └── Project progress = 100%                                     │
│         └── State: CLOSED                                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 📁 Complete File Structure

```
custom_addons/
│
├── executionpm_core/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── SUMMARY.md
│   ├── data/
│   │   ├── execution_project_type_data.xml
│   │   ├── execution_sector_data.xml
│   │   └── ir_sequence_data.xml
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution_project.py
│   │   ├── execution_project_type.py
│   │   ├── execution_sector.py
│   │   └── execution_funding_source.py
│   ├── security/
│   │   ├── executionpm_security.xml
│   │   └── ir.model.access.csv
│   ├── static/description/
│   │   └── icon.svg
│   └── views/
│       ├── execution_project_views.xml
│       ├── execution_project_type_views.xml
│       ├── execution_sector_views.xml
│       ├── execution_funding_source_views.xml
│       └── menu_views.xml
│
├── executionpm_planning/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── SUMMARY.md
│   ├── models/
│   │   ├── __init__.py
│   │   ├── execution_planning.py
│   │   ├── execution_planning_lot.py
│   │   ├── execution_planning_task.py
│   │   └── project_project.py
│   ├── security/
│   │   ├── executionpm_planning_security.xml
│   │   └── ir.model.access.csv
│   └── views/
│       ├── execution_planning_views.xml
│       ├── execution_planning_lot_views.xml
│       ├── execution_planning_task_views.xml
│       ├── project_project_views.xml
│       └── menu_views.xml
│
└── executionpm_execution/
    ├── __init__.py
    ├── __manifest__.py
    ├── SUMMARY.md
    ├── models/
    │   ├── __init__.py
    │   ├── execution_progress.py
    │   └── execution_planning_task.py
    ├── security/
    │   ├── executionpm_execution_security.xml
    │   └── ir.model.access.csv
    └── views/
        ├── execution_progress_views.xml
        ├── execution_planning_task_views.xml
        └── menu_views.xml
```

---

# 🚀 Installation Order

Install modules in this order (dependencies are handled automatically):

1. `executionpm_core` - Base module
2. `executionpm_planning` - Depends on core
3. `executionpm_execution` - Depends on planning

**Command:**
```bash
./odoo-bin -c odoo.conf -i executionpm_core,executionpm_planning,executionpm_execution -d your_database
```

---

# 🔐 Security Summary

| Group | Core | Planning | Execution |
|-------|------|----------|-----------|
| User | View projects, basic edits | Create/edit own planning (draft) | Create/edit own declarations |
| Validator | - | - | Review & validate progress |
| Manager | Full project control | Approve/reject planning | Full declaration control |
| Administrator | System config | - | - |

---

*Execution PM System v18.0.1.0.0 - Complete Documentation*

---

# 📘 FULL USER GUIDE & WORKFLOW MANUAL

This section provides a step-by-step guide on how to use the Execution PM system, including every attribute and its purpose.

## 1. CORE MODULE: Project Setup & Initialization

### Getting Started
The lifecycle begins in the **Core Module**. This is where projects are defined and categorized.

### Step-by-Step:
1.  **Navigate to**: `Execution PM > Projects > All Projects`.
2.  **Create a New Project**:
    -   **Is Execution Project (Boolean)**: Must be checked to enable the infrastructure-specific features.
    -   **National Project Code (Read-only)**: Auto-generated upon confirmation. Format: `[TYPE]-[SECTOR]-[YEAR]-[SEQ]`.
    -   **Project Type (Many2one)**: Select from Water, Energy, Transport, etc. This influences the code generation.
    -   **Sector (Many2one)**: Define the geographic region (e.g., Dakar, Thiès).
    -   **Total Budget (Monetary)**: The total approved amount for the project.
    -   **Primary Funding Source (Many2one)**: Who is paying? (e.g., WB, AFDB, State Budget).
    -   **Contracting Authority (Partner)**: The owner of the project (e.g., Ministry of Water).
    -   **Main Contractor (Partner)**: The company performing the work.
3.  **Confirm the Project**: Click **"Set to Planned"**. The project state moves from `Draft` to `Planned`.

### Attributes Reference:
-   **Execution Progress (%)**: Calculated automatically based on weighted validated tasks.
-   **Physical Progress (%)**: Manual estimate of actual physical work done.
-   **Financial Progress (%)**: Spent Amount / Total Budget.
-   **State Reasoning**: Audit field capturing why a project was suspended or moved to "At Risk".

---

## 2. PLANNING MODULE: The Master Schedule

### Getting Started
Before work can start, a contractor must submit a detailed planning.

### Step-by-Step:
1.  **Navigate to**: `Execution PM > Planning > Execution Plans`.
2.  **Create a Planning Document**:
    -   Link it to an active `Planned` project.
3.  **Build the Hierarchy**:
    -   **Lots**: Group tasks into work packages (e.g., "Lot 1: Earthworks").
    -   **Tasks**: Create granular activities.
    -   **Physical Weight (Float)**: **CRITICAL**. Each task must have a weight (e.g., 5.0). The sum of all task weights in the planning must equal exactly **100.00%**.
    -   **Planned Dates**: Start and end dates for each task.
4.  **Submission**: The Contractor clicks **"Submit"**.
5.  **Review**: The PMO/Manager reviews the planning.
    -   **Approve**: Project state moves to `Running`. Execution can now begin.
    -   **Reject**: Planning goes back to `Draft` for corrections.

### Attributes Reference:
-   **Total Physical Weight**: Live sum of all task weights. Must be 100 for submission.
-   **Planning Dates**: Start and end dates derived from the earliest and latest tasks.

---

## 3. EXECUTION MODULE: Declaring Progress

### Getting Started
Once the project is `Running`, the Contractor declares progress as work is completed.

### Step-by-Step:
1.  **Navigate to**: `Execution PM > Execution > Progress Declarations`.
2.  **Declare Progress**:
    -   **Task (Many2one)**: Select an approved task.
    -   **Declared Percentage (Float)**: Cumulative percentage (e.g., 30% if 30% of that task is done).
    -   **Previous Percentage (Computed)**: Last validated percentage.
    -   **Incremental Percentage (Computed)**: Difference between Declared and Previous.
    -   **Proof Attachments (Many2many)**: **MANDATORY**. You must upload photos or signed PVs to prove the work.
    -   **Description (Text)**: Detail what was achieved.
3.  **Submit**: Click **"Submit for Review"**. State moves to `Submitted`.

### Attributes Reference:
-   **Quantity Executed**: Physical metric (e.g., "500" for 500 meters).
-   **Quantity Unit**: Measurement unit (e.g., "M", "M3").

---

## 4. VALIDATION MODULE: Audit & Verification

### Getting Started
The Validator (PMO/Bureau of Control) ensures the declarations are truthful.

### Step-by-Step:
1.  **Navigate to**: `Execution PM > Execution > To Review`.
2.  **Open a Declaration**:
    -   Review the proof documents and description.
3.  **Execute Decision**:
    -   **Validate**:
        -   Updates the task's `Actual Progress`.
        -   Recalculates Project `Overall Progress`.
        -   Creates an **Immutable Audit Record**.
    -   **Request Correction**: Return to Contractor with a comment.
    -   **Reject**: Marks as invalid.

### Attributes Reference:
-   **Validation Hash (Read-only)**: A unique SHA-256 integrity hash for the record.
-   **Snapshot Fields**: Captures exactly what the percentages were at the time of validation.

---

## 5. ALERTS & MONITORING

### How it Works
The system automatically runs background checks (Cron jobs) every night.

### Alert Types:
-   **Task Delay**: Triggered if a task's end date has passed but progress < 100%.
-   **Inactivity**: Triggered if a `Running` project has no validated progress for X days.
-   **Inconsistency**: Triggered if there is a major gap between Planned vs Actual progress.

### Managing Alerts:
1.  **Acknowledge**: Accept that the issue has been noted.
2.  **Start Progress**: Mark as being worked on.
3.  **Resolve**: Close the alert after fixing the underlying issue.

---

## 6. DASHBOARDS & KPI SUMMARY

### Views Available:
-   **Project Dashboard**: Kanban view of all projects with color-coded alerts (Red for High Risk).
-   **Contractor Dashboard**: Focuses on tasks to declare and pending corrections.
-   **PMO Dashboard**: Focuses on items awaiting validation and system-wide delays.

### Key Metrics:
-   **Project Health**: Based on progress vs. elapsed time.
-   **Validation Accuracy**: Tracking of how many declarations are rejected vs validated.

---

*End of User Guide - Execution PM System*

