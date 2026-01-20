# Execution PM - Validation Module Summary

**Module Name:** `executionpm_validation`  
**Version:** 18.0.1.0.0  
**Created:** January 20, 2026  
**License:** LGPL-3

---

## 📋 Overview

This module formalizes the validation process with immutable audit trails, separating validation authority from declaration authority. All validation decisions are timestamped, hashed for integrity, and cannot be modified after creation.

---

## 📁 File Structure

```
executionpm_validation/
├── __init__.py
├── __manifest__.py
├── SUMMARY.md
├── models/
│   ├── __init__.py
│   ├── execution_validation.py       # Immutable validation records
│   ├── execution_progress.py         # Extended with correction workflow
│   ├── execution_planning_task.py    # Validation stats
│   └── project_project.py            # Project validation stats
├── wizards/
│   ├── __init__.py
│   ├── validation_wizard.py          # Reject/Correction wizard
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

## 🗃️ Key Model: `execution.validation`

**Immutable validation record** that cannot be modified or deleted after creation.

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

### Immutability Features
- ❌ Cannot be modified after creation (raises `UserError`)
- ❌ Cannot be deleted (raises `UserError`)
- ✅ Integrity hash generated on creation
- ✅ Snapshot of progress values preserved

---

## 🚦 Extended Workflow

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
                                              ┌───────────┐
                                              │ Resubmit  │
                                              └───────────┘
```

### New State: `correction_requested`
- Validator can request specific corrections
- Contractor makes corrections and resubmits
- Tracks correction round count
- Preserves all correction comments in audit trail

---

## 🔐 Validation Authority Rules

| Authority | Can Declare | Can Validate | Can Reject | Can Request Correction |
|-----------|-------------|--------------|------------|------------------------|
| **User** (Contractor) | ✅ | ❌ | ❌ | ❌ |
| **Validator** (PMO) | ❌ | ✅ | ✅ | ✅ |
| **Manager** | ✅ | ✅ | ✅ | ✅ |

### Key Security Rules
1. **Separation of Authority**: Validators cannot validate their own declarations
2. **Mandatory Comments**: Rejection and correction require meaningful comments (10+ chars)
3. **Immutable Records**: Validation decisions cannot be changed
4. **Audit Trail**: All decisions are permanently recorded

---

## 📊 Automatic KPI Updates

When a declaration is **validated**:

1. **Task Progress**: `task.actual_progress` = `declaration.declared_percentage`
2. **Project Progress**: Weighted average of all task progress
   ```
   project.execution_progress = Σ(task.actual_progress × task.weight) / Σ(task.weight)
   ```

---

## 🔍 Audit Trail Access

**Menu**: Execution PM → Validation → Audit Trail

Shows all validation decisions with:
- Timestamp
- Validator name and role
- Decision type
- Progress snapshot
- Integrity hash
- Comments

**Note**: This view is read-only. Records cannot be created, edited, or deleted from the UI.

---

## 🚀 Usage Flow

### For Validators (PMO/Control Office)

1. Go to **Execution** → **To Review**
2. Open a submitted declaration
3. Click **"Start Review"** to move to Under Review
4. Review the declaration and attachments
5. Choose action:
   - **"Validate"** → Creates validation record, updates KPIs
   - **"Request Correction"** → Opens wizard, requires comment
   - **"Reject"** → Opens wizard, requires comment

### For Contractors

1. If "Correction Requested":
   - View correction comments
   - Make required changes
   - Click **"Resubmit After Correction"**
2. If "Rejected":
   - View rejection reason
   - May create new declaration if appropriate

---

*Generated by Execution PM Validation v18.0.1.0.0*
