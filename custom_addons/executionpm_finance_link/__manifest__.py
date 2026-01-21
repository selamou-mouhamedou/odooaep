{
    'name': 'Execution PM - Finance Link',
    'version': '1.0',
    'category': 'Construction/Accounting',
    'summary': 'Link Execution Progress with Financial Operations',
    'description': """
        Integrates Execution PM with Accounting.
        - Links Invoices/Bills to Execution Progress Declarations.
        - Blocks payment/invoice validation if linked progress is not validated.
    """,
    'author': 'Antigravity',
    'depends': [
        'account',
        'analytic',
        'executionpm_core',
        'executionpm_execution',
        'executionpm_validation',
    ],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
