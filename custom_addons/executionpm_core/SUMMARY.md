# Execution PM Core - Module Summary

**Module Name:** `executionpm_core`  
**Version:** 18.0.1.0.0  
**Created:** January 20, 2026  
**License:** LGPL-3

---

## 📋 Overview

This module extends Odoo 18's project management for **public and private infrastructure projects** including water, energy, public works, transportation, telecommunications, and more.

---

## 📁 File Structure

```
executionpm_core/
├── __init__.py                           # Module init
├── __manifest__.py                       # Module manifest
├── README.md                             # Documentation
├── SUMMARY.md                            # This file
│
├── data/
│   ├── execution_project_type_data.xml   # 10 pre-loaded project types
│   ├── execution_sector_data.xml         # Sample hierarchical sectors
│   └── ir_sequence_data.xml              # Auto-increment for project codes
│
├── models/
│   ├── __init__.py
│   ├── execution_project.py              # Extended project.project model
│   ├── execution_project_type.py         # Project type classification
│   ├── execution_sector.py               # Geographic sectors (hierarchical)
│   └── execution_funding_source.py       # Funding sources
│
├── security/
│   ├── executionpm_security.xml          # Security groups & record rules
│   └── ir.model.access.csv               # Model access rights
│
├── static/
│   └── description/
│       └── icon.svg                      # Module icon
│
└── views/
    ├── execution_project_views.xml       # Project list/form/kanban views
    ├── execution_project_type_views.xml  # Project type views
    ├── execution_sector_views.xml        # Sector views
    ├── execution_funding_source_views.xml # Funding source views
    └── menu_views.xml                    # Menu structure
```

---

## 🗃️ Models Created

### 1. `execution.project.type`
Categorizes infrastructure projects.

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Type name (translatable) |
| `code` | Char | Unique code (e.g., WAT, ENE, PUB) |
| `description` | Text | Description |
| `icon` | Char | Font Awesome icon class |
| `color` | Integer | Kanban color |
| `project_count` | Integer | Computed count of projects |

**Pre-loaded Types:**
- Water Infrastructure (WAT)
- Energy Infrastructure (ENE)
- Public Works (PUB)
- Transportation (TRA)
- Telecommunications (TEL)
- Education Infrastructure (EDU)
- Health Infrastructure (HEA)
- Environmental (ENV)
- Housing (HOU)
- Other Infrastructure (OTH)

---

### 2. `execution.sector`
Geographic/administrative sectors with hierarchy support.

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Sector name |
| `code` | Char | Unique code |
| `parent_id` | Many2one | Parent sector |
| `child_ids` | One2many | Child sectors |
| `complete_name` | Char | Computed hierarchical name |
| `country_id` | Many2one | Country |
| `state_id` | Many2one | State/Province |
| `project_count` | Integer | Computed count of projects |

---

### 3. `execution.funding.source`
Tracks funding origins for projects.

| Field | Type | Description |
|-------|------|-------------|
| `name` | Char | Funding source name |
| `code` | Char | Unique code |
| `funding_type` | Selection | Type: government, international, private, ppp, loan, grant, mixed, other |
| `partner_id` | Many2one | Funding organization |
| `currency_id` | Many2one | Currency |
| `project_count` | Integer | Computed count |
| `total_funded_amount` | Monetary | Total amount funded |

---

### 4. `project.project` (Extended)
Adds execution-specific fields to the standard project model.

#### Identification Fields
| Field | Type | Description |
|-------|------|-------------|
| `is_execution_project` | Boolean | Flag for execution projects |
| `national_project_code` | Char | Auto-generated unique code |
| `execution_project_type_id` | Many2one | Project type |

#### Location Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_sector_id` | Many2one | Sector |
| `execution_location` | Char | Specific location |
| `execution_latitude` | Float | GPS latitude |
| `execution_longitude` | Float | GPS longitude |
| `execution_country_id` | Many2one | Related country |

#### Financial Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_budget` | Monetary | Total approved budget |
| `execution_currency_id` | Many2one | Currency |
| `execution_funding_source_id` | Many2one | Primary funding source |
| `execution_committed_amount` | Monetary | Committed/contracted amount |
| `execution_spent_amount` | Monetary | Actually spent |
| `execution_budget_remaining` | Monetary | Computed remaining |
| `execution_budget_utilization` | Float | Computed utilization % |

#### Lifecycle State
| Field | Type | Description |
|-------|------|-------------|
| `execution_state` | Selection | draft, planned, running, at_risk, suspended, closed |
| `execution_state_changed_date` | Date | When state was changed |
| `execution_state_changed_by` | Many2one | Who changed the state |
| `execution_state_reason` | Text | Reason for state change |

#### Timeline Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_planned_start` | Date | Planned start date |
| `execution_planned_end` | Date | Planned end date |
| `execution_actual_start` | Date | Actual start date |
| `execution_actual_end` | Date | Actual end date |
| `execution_duration_planned` | Integer | Computed planned days |
| `execution_duration_actual` | Integer | Computed actual days |

#### Progress Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_progress` | Float | Overall progress (0-100%) |
| `execution_physical_progress` | Float | Physical work progress |
| `execution_financial_progress` | Float | Computed from spending |

#### Stakeholder Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_contracting_authority_id` | Many2one | Government/owner entity |
| `execution_contractor_id` | Many2one | Main contractor |
| `execution_supervisor_id` | Many2one | Supervising consultant |

#### Description Fields
| Field | Type | Description |
|-------|------|-------------|
| `execution_objective` | Text | Project objective |
| `execution_scope` | Html | Project scope of work |
| `execution_notes` | Html | Additional notes |

---

## 🔄 Lifecycle State Machine

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌─────────┐
│  DRAFT  │────▶│ PLANNED  │────▶│ RUNNING  │────▶│ CLOSED  │
└─────────┘     └──────────┘     └──────────┘     └─────────┘
                     │                │                 ▲
                     │                ▼                 │
                     │         ┌───────────┐            │
                     └────────▶│  AT RISK  │────────────┤
                               └───────────┘            │
                                     │                  │
                                     ▼                  │
                               ┌───────────┐            │
                               │ SUSPENDED │────────────┘
                               └───────────┘
```

**State Transition Buttons:**
- `Plan Project` - Draft → Planned (requires dates & budget)
- `Start Execution` - Planned → Running (sets actual start)
- `Flag At Risk` - Running → At Risk (requires reason)
- `Suspend` - Running/At Risk → Suspended (requires reason)
- `Resume` - At Risk/Suspended → Running
- `Close Project` - Running/At Risk/Suspended → Closed (requires 100% progress)
- `Reset to Draft` - Planned → Draft (admin only)

---

## 🔐 Security Groups

| Group | XML ID | Permissions |
|-------|--------|-------------|
| **User** | `group_executionpm_user` | View & edit own projects |
| **Validator** | `group_executionpm_validator` | + Validate progress |
| **Manager** | `group_executionpm_manager` | + Full project access, state changes |
| **Administrator** | `group_executionpm_admin` | + Configuration management |

---

## 🎯 National Project Code Format

Auto-generated format: `TYPE-SECTOR-YEAR-SEQUENCE`

**Example:** `WAT-NO-2026-0001`
- `WAT` = Water Infrastructure (from project type)
- `NO` = North Region (first 2 chars of sector code)
- `2026` = Current year
- `0001` = Sequential number

---

## 📱 Views Created

| View | Type | Description |
|------|------|-------------|
| Execution Projects List | list | Projects with state badges, progress bars |
| Execution Projects Form | form (inherited) | Extended with "Execution Details" tab |
| Execution Projects Kanban | kanban | Grouped by state, shows progress |
| Project Types List/Kanban/Form | list, kanban, form | CRUD for project types |
| Sectors List/Form | list, form | Hierarchical sector management |
| Funding Sources List/Kanban/Form | list, kanban, form | Funding source management |

---

## 📊 Menu Structure

```
Execution PM (Root Menu)
├── Projects
│   ├── All Projects
│   └── Project Dashboard
│
└── Configuration (Admin only)
    └── General
        ├── Project Types
        ├── Sectors
        └── Funding Sources
```

---

## 🔗 Dependencies

- `base` - Core Odoo
- `project` - Standard project module
- `mail` - Messaging and tracking

---

## 🚀 Usage

1. Go to **Execution PM** app
2. Create a new project and check **"Is Execution Project"**
3. Fill in project type, sector, budget, and timeline
4. Use state buttons to progress through the lifecycle
5. Track progress and budget utilization

---

## 📝 Best Practices Followed

✅ Modular architecture  
✅ Clean model separation  
✅ Explicit states with workflow  
✅ Access rights via `ir.model.access.csv`  
✅ Record rules for data security  
✅ No hard-coded values  
✅ Full audit trail with `mail.thread`  
✅ Computed fields for derived data  
✅ SQL constraints for data integrity  
✅ Translatable strings with `_()` function

---

*Generated by Execution PM Core v18.0.1.0.0*
