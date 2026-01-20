# -*- coding: utf-8 -*-
{
    'name': 'Execution PM - Progress Execution',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Track and validate contractor execution progress declarations',
    'description': """
Execution Project Management - Progress Execution
==================================================

Allows contractors to declare execution progress per task with mandatory proof.

Key Features:
-------------
* Progress Declaration per Task
* Mandatory attachments (proof of work)
* Multi-step validation workflow
* Validated progress updates project KPIs
* Audit trail of all declarations
    """,
    'author': 'Your Company',
    'depends': [
        'executionpm_planning',
        'mail',
    ],
    'data': [
        'security/executionpm_execution_security.xml',
        'security/ir.model.access.csv',
        'views/execution_progress_views.xml',
        'views/execution_planning_task_views.xml',
        'views/progress_computation_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
