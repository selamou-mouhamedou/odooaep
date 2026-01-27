# Execution PM - Role-Based Access Control (RBAC) Documentation

## Overview

This document describes the comprehensive Role-Based Access Control (RBAC) system implemented in the Execution PM module suite. The system ensures that each user can only see and modify data relevant to their role.

---

## Role Hierarchy

```
Administrator (Full Access)
    │
    ├── PMO (Project Management Office)
    │       └── Control Office
    │               └── Base Access
    │
    └── Authority (Monitoring)
            └── Base Access
    
Contractor
    └── Base Access
```

---

## Roles and Permissions

### 1. Administrator (`group_executionpm_admin`)

**Description:** Full access to all Execution PM data, projects, tasks, and administrative configurations.

| Access Type | Permission |
|------------|------------|
| **Projects** | Create, Read, Write, Delete - All projects |
| **Tasks** | Create, Read, Write, Delete - All tasks |
| **Planning** | Create, Read, Write, Delete - All planning documents |
| **Progress** | Create, Read, Write, Delete - All declarations |
| **Validation** | Create, Read, Write, Delete - All records |
| **Alerts** | Create, Read, Write, Delete - All alerts |
| **Financial Data** | Full access to budget, spending, funding information |
| **User Management** | Can manage user access and role assignments |
| **Reference Data** | Manage sectors, project types, funding sources |

### 2. PMO - Project Management Office (`group_executionpm_pmo`)

**Description:** Can see all projects and tasks. Can validate or reject task progress submissions but cannot modify task data directly.

| Access Type | Permission |
|------------|------------|
| **Projects** | Read all, Write status updates only |
| **Tasks** | Read all, Write status updates only |
| **Planning** | Create, Read, Write, Delete - Non-approved planning |
| **Progress** | Read all, Write (for validation actions only) |
| **Validation** | Create validation records (except own declarations) |
| **Alerts** | Create, Read, Write alerts |
| **Financial Data** | ❌ NO ACCESS |

**Key Restrictions:**
- Cannot modify task data directly
- Cannot validate their own progress declarations
- Cannot access financial/contractual data

### 3. Control Office (`group_executionpm_control_office`)

**Description:** Can see all tasks in assigned projects. Can provide feedback and comments but cannot modify task data or validate progress.

| Access Type | Permission |
|------------|------------|
| **Projects** | Read assigned projects only |
| **Tasks** | Read tasks in assigned projects only |
| **Planning** | Read planning for assigned projects |
| **Progress** | Read all declarations |
| **Validation** | Read validation records (audit trail) |
| **Alerts** | Read alerts for assigned projects |
| **Financial Data** | ❌ NO ACCESS |

**Key Restrictions:**
- Can only view projects they are assigned to (via followers or supervisor)
- Cannot modify any data (read-only access)
- Cannot approve or reject task progress
- Feedback via chatter/comments only

### 4. Contractor (`group_executionpm_contractor`)

**Description:** Can only see tasks assigned to them within their project. Can update progress on tasks they are responsible for.

| Access Type | Permission |
|------------|------------|
| **Projects** | Read own projects only |
| **Tasks** | Read own assigned tasks only |
| **Planning** | Read planning for own projects |
| **Progress** | Create/Edit own draft/rejected declarations |
| **Validation** | Read own validation history |
| **Alerts** | Read alerts for own projects |
| **Financial Data** | ❌ NO ACCESS |

**Key Restrictions:**
- Cannot view other contractors' tasks or projects
- Cannot approve progress or task status
- Can only modify draft or rejected declarations (not submitted/validated)
- Cannot delete any records

### 5. Authority (`group_executionpm_authority`)

**Description:** Oversight entities (Ministry, Government agencies) that can view all data for monitoring purposes but cannot modify anything.

| Access Type | Permission |
|------------|------------|
| **Projects** | Read all projects |
| **Tasks** | Read all tasks |
| **Planning** | Read all planning documents |
| **Progress** | Read all declarations |
| **Validation** | Read all validation records |
| **Alerts** | Read all alerts |
| **Financial Data** | ❌ NO ACCESS |

**Key Restrictions:**
- Strictly read-only access
- Cannot modify any data
- Cannot approve or reject tasks
- Monitoring and auditing purposes only

---

## Financial Data Access

**Financial fields are restricted to Administrator only:**

- `execution_budget` - Total Budget
- `execution_currency_id` - Currency
- `execution_funding_source_id` - Funding Source
- `execution_committed_amount` - Committed Amount
- `execution_spent_amount` - Spent Amount
- `execution_budget_remaining` - Remaining Budget
- `execution_budget_utilization` - Budget Utilization %
- `execution_financial_progress` - Financial Progress %

Non-administrators will not see these fields in:
- List views
- Form views
- Kanban views
- Reports

---

## Record Rules Summary

### Projects (`project.project`)

| Role | Domain Filter | Permissions |
|------|--------------|-------------|
| Base | `is_execution_project = True` | Read |
| Contractor | Own projects (via contractor_id or follower) | Read |
| Control Office | Assigned projects (user_id, followers, supervisor) | Read |
| Authority | All execution projects | Read |
| PMO | All execution projects (running/at_risk/planned for write) | Read, Write |
| Admin | All projects | Full |

### Planning (`execution.planning`)

| Role | Domain Filter | Permissions |
|------|--------------|-------------|
| Contractor | Own project planning | Read |
| Control Office | Assigned project planning | Read |
| Authority | All planning | Read |
| PMO | Non-approved planning (draft/submitted/rejected) | Full |
| Admin | All planning | Full |

**Note:** Approved planning documents are read-only for everyone except Admin.

### Progress Declarations (`execution.progress`)

| Role | Domain Filter | Permissions |
|------|--------------|-------------|
| Contractor | Own declarations (draft/rejected for edit) | Read, Create, Write (limited) |
| Control Office | All declarations | Read |
| Authority | All declarations | Read |
| PMO | Submitted/under_review for validation | Read, Write (state changes) |
| Admin | All declarations | Full |

**Note:** Validated declarations are read-only for everyone except Admin.

### Validation Records (`execution.validation`)

| Role | Domain Filter | Permissions |
|------|--------------|-------------|
| Contractor | Own task validations | Read |
| Control Office | All validations | Read |
| Authority | All validations | Read |
| PMO | Not own declarations (separation of concerns) | Read, Create |
| Admin | All validations | Full |

**Note:** Validation records are immutable (write/unlink blocked by model constraints).

---

## State-Based Access Control

### Progress Declaration States

```
draft → submitted → under_review → validated/rejected
```

| State | Contractor | Control Office | PMO | Authority | Admin |
|-------|-----------|----------------|-----|-----------|-------|
| draft | RW | R | R | R | Full |
| submitted | R | R | RW | R | Full |
| under_review | R | R | RW | R | Full |
| validated | R (immutable) | R | R | R | Full |
| rejected | RW | R | R | R | Full |

### Planning States

```
draft → submitted → approved/rejected
```

| State | Contractor | Control Office | PMO | Authority | Admin |
|-------|-----------|----------------|-----|-----------|-------|
| draft | R | R | Full | R | Full |
| submitted | R | R | Full | R | Full |
| approved | R (immutable) | R | R | R | Full |
| rejected | R | R | Full | R | Full |

---

## Security Files Location

| Module | ACL File | Record Rules File |
|--------|----------|-------------------|
| executionpm_core | `security/ir.model.access.csv` | `security/executionpm_security.xml` |
| executionpm_planning | `security/ir.model.access.csv` | `security/executionpm_planning_security.xml` |
| executionpm_execution | `security/ir.model.access.csv` | `security/executionpm_execution_security.xml` |
| executionpm_validation | `security/ir.model.access.csv` | `security/executionpm_validation_security.xml` |
| executionpm_alerts | `security/ir.model.access.csv` | `security/executionpm_alerts_security.xml` |

---

## User Assignment

To assign a user to a role:

1. Navigate to **Settings > Users & Companies > Users**
2. Select the user
3. Scroll to **Execution PM** section
4. Select the appropriate role checkbox:
   - Base Access (automatically assigned when selecting any role)
   - Contractor
   - Control Office
   - PMO
   - Authority
   - Administrator

**Important:** Only assign ONE primary role per user (except Administrator which includes PMO and Authority).

---

## Testing RBAC

### Test Scenarios

1. **Contractor Access Test:**
   - Create a user with Contractor role
   - Assign them to a project via contractor_id
   - Verify they can only see their own tasks
   - Verify they can create/edit draft progress declarations
   - Verify they cannot see financial data

2. **PMO Access Test:**
   - Create a user with PMO role
   - Verify they can see all projects and tasks
   - Verify they can validate/reject progress declarations
   - Verify they cannot modify task data directly
   - Verify they cannot see financial data

3. **Authority Access Test:**
   - Create a user with Authority role
   - Verify they can view all data
   - Verify they cannot modify any data
   - Verify they cannot see financial data

4. **Admin Access Test:**
   - Create a user with Administrator role
   - Verify full access to all features
   - Verify access to financial data

---

## Common Issues and Solutions

### Issue: User cannot see any projects
**Solution:** Ensure the user has at least "Base Access" role and is either:
- Assigned as project manager (user_id)
- Added as a follower (message_partner_ids)
- Set as supervisor (execution_supervisor_id)
- Associated via contractor (execution_contractor_id)

### Issue: Contractor sees other contractors' tasks
**Solution:** Check the project's `execution_contractor_id` field is correctly set.

### Issue: PMO cannot validate progress
**Solution:** Ensure the progress declaration is in 'submitted' or 'under_review' state.

### Issue: User sees financial data when they shouldn't
**Solution:** Clear browser cache and reload. Check if user has Administrator role assigned.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-27 | Initial RBAC implementation |

