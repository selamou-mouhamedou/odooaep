# -*- coding: utf-8 -*-
{
    'name': 'Execution PM - Validation Authority',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Formal validation workflow with immutable audit trail',
    'description': """
Execution Project Management - Validation Module
=================================================

Separates validation authority from declaration authority with full audit trail.

Key Features:
-------------
* Dedicated Validation Records (immutable)
* PMO/Control Office validation authority
* Request Correction workflow
* Timestamped, immutable validation decisions
* Automatic KPI updates on validation
* Complete audit trail
    """,
    'author': 'Your Company',
    'depends': [
        'executionpm_execution',
    ],
    'data': [
        'security/executionpm_validation_security.xml',
        'security/ir.model.access.csv',
        'wizards/validation_wizard_views.xml',
        'views/execution_validation_views.xml',
        'views/execution_progress_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
