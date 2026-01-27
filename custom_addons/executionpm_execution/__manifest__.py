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
        'executionpm_core',
        'executionpm_planning',
        'mail',
        'board',
    ],
    'data': [
        'security/executionpm_execution_security.xml',
        'security/ir.model.access.csv',
        'views/execution_progress_views.xml',
        'views/execution_planning_task_views.xml',
        'views/progress_computation_views.xml',
        'views/project_task_views.xml',
        'views/project_project_views.xml',
        'views/dashboard_pmo_views.xml',
        'views/dashboard_contractor_views.xml',
        'views/menu_views.xml',
        'data/fix_dashboard_domains.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
}
