# Execution PM Core

**Odoo 18 Module for Infrastructure Project Execution Management**

## Overview

This module extends Odoo's project management capabilities for managing public and private infrastructure projects, including:

- Water infrastructure
- Energy infrastructure
- Public works
- Transportation
- Telecommunications
- And more...

## Features

### Project Management
- **Extended Project Model**: Adds execution-specific fields to `project.project`
- **National Project Code**: Unique, auto-generated project identifier
- **Project Types**: Categorize projects by infrastructure type
- **Sectors**: Geographic/administrative location tracking
- **Funding Sources**: Track project funding origins

### Lifecycle Management
- **Six Lifecycle States**: draft → planned → running → at_risk/suspended → closed
- **State Transitions**: Validated workflow with proper access controls
- **Audit Trail**: Full tracking of state changes with timestamps and user info

### Financial Tracking
- **Budget Management**: Total budget, committed, and spent amounts
- **Budget Utilization**: Automatic calculation and progress bars
- **Multi-currency Support**: Works with Odoo's currency system

### Progress Tracking
- **Overall Progress**: Combined project progress
- **Physical Progress**: Physical work completion
- **Financial Progress**: Budget utilization percentage

## Installation

1. Copy the `executionpm_core` folder to your Odoo addons path
2. Update the apps list: `Apps > Update Apps List`
3. Search for "Execution PM Core" and install

## Configuration

After installation:

1. Go to **Execution PM > Configuration**
2. Review/customize **Project Types** (pre-loaded with common infrastructure types)
3. Define your **Sectors** (geographic regions)
4. Set up **Funding Sources** (donors, government, PPP, etc.)

## Security Groups

| Group | Description |
|-------|-------------|
| User | Basic access to view and edit own projects |
| Validator | Can validate progress declarations |
| Manager | Full project management access |
| Administrator | Full system access including configuration |

## Dependencies

- `base`
- `project`
- `mail`

## License

LGPL-3

## Author

Your Company

---

*Part of the Execution PM Suite for infrastructure project management.*
