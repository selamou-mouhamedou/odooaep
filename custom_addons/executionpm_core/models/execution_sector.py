# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ExecutionSector(models.Model):
    """
    Execution Sector
    
    Defines geographic or administrative sectors/regions for projects.
    Supports hierarchical structure (parent-child relationships).
    """
    _name = 'execution.sector'
    _description = 'Execution Sector'
    _order = 'complete_name'
    _parent_name = 'parent_id'
    _parent_store = True
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Sector Name',
        required=True,
        tracking=True,
        translate=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique sector code',
    )
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True,
        recursive=True,
    )
    parent_id = fields.Many2one(
        comodel_name='execution.sector',
        string='Parent Sector',
        index=True,
        ondelete='restrict',
        tracking=True,
    )
    parent_path = fields.Char(
        index=True,
    )
    child_ids = fields.One2many(
        comodel_name='execution.sector',
        inverse_name='parent_id',
        string='Child Sectors',
    )
    description = fields.Text(
        string='Description',
        translate=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        tracking=True,
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State/Province',
        domain="[('country_id', '=', country_id)]",
        tracking=True,
    )
    project_count = fields.Integer(
        string='Project Count',
        compute='_compute_project_count',
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Sector code must be unique!'),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute hierarchical complete name."""
        for record in self:
            if record.parent_id:
                record.complete_name = f'{record.parent_id.complete_name} / {record.name}'
            else:
                record.complete_name = record.name

    @api.depends('name')
    def _compute_project_count(self):
        """Compute the number of projects in each sector."""
        for record in self:
            record.project_count = self.env['project.project'].search_count([
                ('execution_sector_id', '=', record.id)
            ])

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Prevent circular references in hierarchy."""
        if not self._check_recursion():
            raise ValidationError(
                _('Error! You cannot create recursive sector hierarchy.')
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
        """Display complete hierarchical name."""
        result = []
        for record in self:
            result.append((record.id, record.complete_name or record.name))
        return result
