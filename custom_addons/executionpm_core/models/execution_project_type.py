# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExecutionProjectType(models.Model):
    """
    Execution Project Type
    
    Defines the type/category of infrastructure projects:
    - Water infrastructure
    - Energy infrastructure
    - Public works
    - Transportation
    - Telecommunications
    - etc.
    """
    _name = 'execution.project.type'
    _description = 'Execution Project Type'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Type Name',
        required=True,
        tracking=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique code for this project type (e.g., WAT, ENE, PUB)',
    )
    description = fields.Text(
        string='Description',
        translate=True,
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
    icon = fields.Char(
        string='Icon',
        default='fa-building',
        help='Font Awesome icon class (e.g., fa-water, fa-bolt)',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Project type code must be unique!'),
        ('name_unique', 'UNIQUE(name)', 'Project type name must be unique!'),
    ]

    @api.depends('name')
    def _compute_project_count(self):
        """Compute the number of projects for each type."""
        for record in self:
            record.project_count = self.env['project.project'].search_count([
                ('execution_project_type_id', '=', record.id)
            ])

    @api.constrains('code')
    def _check_code_format(self):
        """Ensure code is uppercase alphanumeric."""
        for record in self:
            if record.code and not record.code.replace('_', '').isalnum():
                raise ValidationError(
                    _('Project type code must be alphanumeric (underscores allowed).')
                )

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
