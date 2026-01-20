# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExecutionFundingSource(models.Model):
    """
    Execution Funding Source
    
    Defines funding sources for infrastructure projects:
    - Government budget
    - International donors
    - Private investment
    - Public-Private Partnership (PPP)
    - Loans
    - etc.
    """
    _name = 'execution.funding.source'
    _description = 'Execution Funding Source'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Funding Source',
        required=True,
        tracking=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique code for this funding source',
    )
    funding_type = fields.Selection(
        selection=[
            ('government', 'Government Budget'),
            ('international', 'International Donor'),
            ('private', 'Private Investment'),
            ('ppp', 'Public-Private Partnership'),
            ('loan', 'Loan/Credit'),
            ('grant', 'Grant'),
            ('mixed', 'Mixed Funding'),
            ('other', 'Other'),
        ],
        string='Funding Type',
        required=True,
        default='government',
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Funding Partner',
        tracking=True,
        help='The organization providing the funding',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    project_count = fields.Integer(
        string='Project Count',
        compute='_compute_project_count',
    )
    total_funded_amount = fields.Monetary(
        string='Total Funded Amount',
        compute='_compute_total_funded_amount',
        currency_field='currency_id',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Funding source code must be unique!'),
    ]

    @api.depends('name')
    def _compute_project_count(self):
        """Compute the number of projects using each funding source."""
        for record in self:
            record.project_count = self.env['project.project'].search_count([
                ('execution_funding_source_id', '=', record.id)
            ])

    @api.depends('name')
    def _compute_total_funded_amount(self):
        """Compute total amount funded across all projects."""
        for record in self:
            projects = self.env['project.project'].search([
                ('execution_funding_source_id', '=', record.id)
            ])
            record.total_funded_amount = sum(projects.mapped('execution_budget'))

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure code is uppercase on create."""
        for vals in vals_list:
            if vals.get('code'):
                vals['code'] = vals['code'].upper()
        return super().create(vals_list)

    def write(self, vals):
        """Ensure code is uppercase on write."""
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        return super().write(vals)

    def name_get(self):
        """Display name with code."""
        result = []
        for record in self:
            name = f'[{record.code}] {record.name}' if record.code else record.name
            result.append((record.id, name))
        return result
