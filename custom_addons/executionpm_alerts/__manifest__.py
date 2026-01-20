# -*- coding: utf-8 -*-
{
    'name': 'ExecutionPM - Alerts',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Automatic Alerts for Execution Project Management',
    'description': """
        ExecutionPM Alerts Module
        =========================
        
        Provides automatic alerting system for execution projects:
        
        - Task delay alerts when threshold exceeded
        - Inactivity alerts when no updates for X days
        - Progress inconsistency alerts
        - Configurable severity levels
        - Automatic email notifications
        - Alert dashboard and management
    """,
    'author': 'ExecutionPM',
    'depends': [
        'mail',
        'executionpm_core',
        'executionpm_planning',
        'executionpm_execution',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/alert_config_data.xml',
        'data/mail_template_data.xml',
        'data/alert_cron_data.xml',
        'views/execution_alert_views.xml',
        'views/execution_alert_config_views.xml',
        'views/project_alert_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
