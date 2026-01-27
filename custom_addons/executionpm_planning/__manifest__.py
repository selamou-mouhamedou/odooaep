# -*- coding: utf-8 -*-
{
    'name': 'Execution PM Planning',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Detailed execution planning for infrastructure projects',
    'description': """
Execution Project Management - Planning Module
===============================================

Manages the detailed execution planning submitted by contractors.

Key Features:
-------------
* Detailed Planning Structure: Project -> Lots -> Tasks
* Tracking of planned dates and duration
* Physical weight allocation (Total must be 100%)
* Approval Workflow: Draft -> Submitted -> Approved/Rejected
* Constraint: Project cannot start without approved planning
* Gantt view support (via standard list/timeline views)
    """,
    'author': 'Your Company',
    'depends': [
        'executionpm_core',
    ],
    'data': [
        'security/executionpm_planning_security.xml',
        'security/ir.model.access.csv',
        'views/execution_planning_views.xml',
        'views/execution_planning_lot_views.xml',
        'views/execution_planning_task_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
