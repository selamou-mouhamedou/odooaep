# -*- coding: utf-8 -*-
{
    'name': 'Execution PM Core',
    'version': '18.0.1.0.1',
    'category': 'Project',
    'summary': 'Core module for infrastructure project execution management',
    'description': """
Execution Project Management - Core Module
===========================================

This module extends Odoo's project management capabilities for infrastructure 
project execution (water, energy, public works, etc.).

Features:
---------
* Extended project model with execution-specific fields
* Project type classification (water, energy, public works, etc.)
* Unique national project code management
* Sector and location tracking
* Budget and funding source management
* Project lifecycle states with audit trail
* Role-based access control

This is the foundation module for the Execution PM suite.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'mail',
        'board',
    ],
    'data': [
        # Security
        'security/executionpm_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/execution_project_type_data.xml',
        'data/execution_sector_data.xml',
        'data/ir_sequence_data.xml',
        # Views (Order matters: Menus first so they can be referenced as parents)
        'views/menu_views.xml',
        'wizards/execution_project_state_wizard_views.xml',
        'views/execution_project_views.xml',
        'views/execution_project_type_views.xml',
        'views/execution_sector_views.xml',
        'views/execution_funding_source_views.xml',
        'views/dashboard_authority_views.xml',
        'views/res_users_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
