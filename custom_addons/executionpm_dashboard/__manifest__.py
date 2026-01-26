{
    'name': 'Execution PM - Dashboards',
    'version': '1.0',
    'category': 'Construction/Reporting',
    'summary': 'Role-based Dashboards for Execution PM',
    'description': """
        Centralized dashboards for Execution PM roles:
        - Authority Dashboard: Strategic overview (KPIs, Global Execution).
        - PMO Dashboard: Operational focus (Validations, Alerts, Delays).
        - Contractor Dashboard: Execution focus (My Tasks, Corrections).
    """,
    'author': 'Antigravity',
    'depends': [
        'web',
        'board',
        'executionpm_core',
        'executionpm_execution',
        'executionpm_alerts',
        'executionpm_validation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/authority_dashboard_views.xml',
        'views/pmo_dashboard_views.xml',
        'views/contractor_dashboard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
