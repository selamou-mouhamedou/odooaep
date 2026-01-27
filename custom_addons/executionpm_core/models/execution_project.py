# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date


class ProjectProject(models.Model):
    """
    Extension of project.project for infrastructure execution management.
    
    Adds:
    - Execution project type
    - National project code (unique, auto-generated)
    - Sector and location
    - Budget and funding source
    - Lifecycle states with workflow
    """
    _inherit = 'project.project'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """
        Global filter: In the context of the Execution PM module,
        hide standard projects that are not marked as infrastructure projects.
        """
        if self.env.context.get('is_execution_pm_context') or self.env.context.get('default_is_execution_project'):
            domain = [('is_execution_project', '=', True), ('national_project_code', '!=', False)] + list(domain)
        return super()._search(domain, offset, limit, order)

    def _register_hook(self):
        """
        Isolation Hook: Automatically untags Odoo standard demo projects 
        from the Execution PM views to keep dashboards clean.
        """
        res = super()._register_hook()
        demo_names = ['Home Construction', 'Office Design', 'Renovations', 'Research & Development']
        demo_projects = self.search([
            ('name', 'in', demo_names),
            ('is_execution_project', '=', True)
        ])
        if demo_projects:
            demo_projects.write({'is_execution_project': False})
        return res

    # -------------------------------------------------------------------------
    # IDENTIFICATION FIELDS
    # -------------------------------------------------------------------------
    is_execution_project = fields.Boolean(
        string='Is Execution Project',
        default=False,
        tracking=True,
        help='Check if this is an infrastructure execution project',
    )
    national_project_code = fields.Char(
        string='National Project Code',
        readonly=True,
        copy=False,
        tracking=True,
        help='Unique national identifier for this project',
    )
    execution_ref_code = fields.Char(
        string='Ref Code',
        tracking=True,
        help='Internal reference code for the project (optional)',
    )
    execution_project_type_id = fields.Many2one(
        comodel_name='execution.project.type',
        string='Project Type',
        tracking=True,
        help='Type of infrastructure project (Water, Energy, etc.)',
    )
    
    # -------------------------------------------------------------------------
    # LOCATION FIELDS
    # -------------------------------------------------------------------------
    execution_sector_id = fields.Many2one(
        comodel_name='execution.sector',
        string='Sector',
        tracking=True,
        help='Geographic/administrative sector for this project',
    )
    execution_location = fields.Char(
        string='Specific Location',
        tracking=True,
        help='Detailed location description',
    )
    execution_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
    )
    execution_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
    )
    execution_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        related='execution_sector_id.country_id',
        store=True,
        readonly=True,
    )
    
    # -------------------------------------------------------------------------
    # FINANCIAL FIELDS
    # -------------------------------------------------------------------------
    execution_budget = fields.Monetary(
        string='Total Budget',
        tracking=True,
        currency_field='execution_currency_id',
        help='Total approved budget for this project',
    )
    execution_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    execution_funding_source_id = fields.Many2one(
        comodel_name='execution.funding.source',
        string='Primary Funding Source',
        tracking=True,
    )
    execution_committed_amount = fields.Monetary(
        string='Committed Amount',
        tracking=True,
        currency_field='execution_currency_id',
        help='Amount committed/contracted so far',
    )
    execution_spent_amount = fields.Monetary(
        string='Spent Amount',
        tracking=True,
        currency_field='execution_currency_id',
        help='Amount actually spent so far',
    )
    execution_budget_remaining = fields.Monetary(
        string='Remaining Budget',
        compute='_compute_budget_remaining',
        store=True,
        currency_field='execution_currency_id',
    )
    execution_budget_utilization = fields.Float(
        string='Budget Utilization (%)',
        compute='_compute_budget_utilization',
        store=True,
        digits=(5, 2),
    )
    
    # -------------------------------------------------------------------------
    # LIFECYCLE STATE
    # -------------------------------------------------------------------------
    execution_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('planned', 'Planned'),
            ('running', 'Running'),
            ('at_risk', 'At Risk'),
            ('suspended', 'Suspended'),
            ('closed', 'Closed'),
        ],
        string='Execution State',
        default='draft',
        tracking=True,
        group_expand='_group_expand_execution_state',
        help='Current lifecycle state of the execution project',
    )
    execution_state_changed_date = fields.Date(
        string='State Changed Date',
        readonly=True,
        tracking=True,
    )
    execution_state_changed_by = fields.Many2one(
        comodel_name='res.users',
        string='State Changed By',
        readonly=True,
        tracking=True,
    )
    execution_state_reason = fields.Text(
        string='State Change Reason',
        tracking=True,
    )
    
    # -------------------------------------------------------------------------
    # TIMELINE FIELDS
    # -------------------------------------------------------------------------
    execution_planned_start = fields.Date(
        string='Planned Start Date',
        tracking=True,
    )
    execution_planned_end = fields.Date(
        string='Planned End Date',
        tracking=True,
    )
    execution_actual_start = fields.Date(
        string='Actual Start Date',
        tracking=True,
    )
    execution_actual_end = fields.Date(
        string='Actual End Date',
        tracking=True,
    )
    execution_duration_planned = fields.Integer(
        string='Planned Duration (Days)',
        compute='_compute_duration_planned',
        store=True,
    )
    execution_duration_actual = fields.Integer(
        string='Actual Duration (Days)',
        compute='_compute_duration_actual',
        store=True,
    )
    execution_delay_days = fields.Integer(
        string='Delay (Days)',
        compute='_compute_delay_days',
        store=True,
    )
    
    # -------------------------------------------------------------------------
    # PROGRESS FIELDS
    # -------------------------------------------------------------------------
    execution_progress = fields.Float(
        string='Overall Progress (%)',
        default=0.0,
        tracking=True,
        digits=(5, 2),
    )
    execution_physical_progress = fields.Float(
        string='Physical Progress (%)',
        default=0.0,
        tracking=True,
        digits=(5, 2),
    )
    execution_financial_progress = fields.Float(
        string='Financial Progress (%)',
        compute='_compute_financial_progress',
        store=True,
        digits=(5, 2),
    )
    
    # -------------------------------------------------------------------------
    # STAKEHOLDER FIELDS
    # -------------------------------------------------------------------------
    execution_contracting_authority_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contracting Authority',
        tracking=True,
        help='Government entity or organization owning the project',
    )
    execution_contractor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Main Contractor',
        tracking=True,
    )
    execution_supervisor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Project Supervisor',
        tracking=True,
        help='Consulting firm or entity supervising the project',
    )
    
    # -------------------------------------------------------------------------
    # DESCRIPTION FIELDS
    # -------------------------------------------------------------------------
    execution_objective = fields.Text(
        string='Project Objective',
        tracking=True,
    )
    execution_scope = fields.Html(
        string='Project Scope',
        tracking=True,
    )
    execution_notes = fields.Html(
        string='Notes',
    )

    # -------------------------------------------------------------------------
    # SQL CONSTRAINTS
    # -------------------------------------------------------------------------
    _sql_constraints = [
        (
            'national_project_code_unique',
            'UNIQUE(national_project_code)',
            'National project code must be unique!'
        ),
        (
            'execution_progress_range',
            'CHECK(execution_progress >= 0 AND execution_progress <= 100)',
            'Progress must be between 0 and 100!'
        ),
        (
            'execution_physical_progress_range',
            'CHECK(execution_physical_progress >= 0 AND execution_physical_progress <= 100)',
            'Physical progress must be between 0 and 100!'
        ),
    ]

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('execution_budget', 'execution_spent_amount')
    def _compute_budget_remaining(self):
        """Compute remaining budget."""
        for project in self:
            project.execution_budget_remaining = (
                project.execution_budget - project.execution_spent_amount
            )

    @api.depends('execution_budget', 'execution_spent_amount')
    def _compute_budget_utilization(self):
        """Compute budget utilization percentage."""
        for project in self:
            if project.execution_budget:
                project.execution_budget_utilization = (
                    (project.execution_spent_amount / project.execution_budget) * 100
                )
            else:
                project.execution_budget_utilization = 0.0

    @api.depends('execution_planned_start', 'execution_planned_end')
    def _compute_duration_planned(self):
        """Compute planned duration in days."""
        for project in self:
            if project.execution_planned_start and project.execution_planned_end:
                delta = project.execution_planned_end - project.execution_planned_start
                project.execution_duration_planned = delta.days
            else:
                project.execution_duration_planned = 0

    @api.depends('execution_actual_start', 'execution_actual_end')
    def _compute_duration_actual(self):
        """Compute actual duration in days."""
        for project in self:
            if project.execution_actual_start:
                end_date = project.execution_actual_end or date.today()
                delta = end_date - project.execution_actual_start
                project.execution_duration_actual = delta.days
            else:
                project.execution_duration_actual = 0

    @api.depends('execution_budget', 'execution_spent_amount')
    def _compute_financial_progress(self):
        """Compute financial progress based on spending."""
        for project in self:
            if project.execution_budget:
                project.execution_financial_progress = (
                    (project.execution_spent_amount / project.execution_budget) * 100
                )
            else:
                project.execution_financial_progress = 0.0

    @api.depends('execution_planned_end', 'execution_actual_end', 'execution_progress')
    def _compute_delay_days(self):
        """Compute current delay days."""
        today = date.today()
        for project in self:
            if project.execution_progress >= 100:
                if project.execution_actual_end and project.execution_planned_end:
                    delay = (project.execution_actual_end - project.execution_planned_end).days
                    project.execution_delay_days = max(0, delay)
                else:
                    project.execution_delay_days = 0
            else:
                if project.execution_planned_end and project.execution_planned_end < today:
                    project.execution_delay_days = (today - project.execution_planned_end).days
                else:
                    project.execution_delay_days = 0

    # -------------------------------------------------------------------------
    # CONSTRAINT METHODS
    # -------------------------------------------------------------------------
    @api.constrains('execution_planned_start', 'execution_planned_end')
    def _check_planned_dates(self):
        """Ensure planned end date is after start date."""
        for project in self:
            if (project.execution_planned_start and project.execution_planned_end and
                    project.execution_planned_end < project.execution_planned_start):
                raise ValidationError(
                    _('Planned end date must be after planned start date.')
                )

    @api.constrains('execution_actual_start', 'execution_actual_end')
    def _check_actual_dates(self):
        """Ensure actual end date is after start date."""
        for project in self:
            if (project.execution_actual_start and project.execution_actual_end and
                    project.execution_actual_end < project.execution_actual_start):
                raise ValidationError(
                    _('Actual end date must be after actual start date.')
                )

    @api.constrains('execution_spent_amount', 'execution_budget')
    def _check_spent_amount(self):
        """Warn if spent amount exceeds budget."""
        for project in self:
            if (project.execution_budget and project.execution_spent_amount and
                    project.execution_spent_amount > project.execution_budget):
                # Log warning but don't block - budget overruns happen
                project.message_post(
                    body=_('Warning: Spent amount exceeds total budget!'),
                    message_type='notification',
                )

    # -------------------------------------------------------------------------
    # GROUP EXPAND
    # -------------------------------------------------------------------------
    @api.model
    def _group_expand_execution_state(self, states, domain, order=None):
        """Expand all states in kanban view."""
        return [key for key, val in self._fields['execution_state'].selection]

    # -------------------------------------------------------------------------
    # CRUD METHODS
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Generate national project code on creation if execution project."""
        for vals in vals_list:
            if vals.get('is_execution_project') and not vals.get('national_project_code'):
                vals['national_project_code'] = self._generate_national_code(vals)
        return super().create(vals_list)

    def write(self, vals):
        """Track state changes with audit info."""
        if 'execution_state' in vals:
            vals['execution_state_changed_date'] = date.today()
            vals['execution_state_changed_by'] = self.env.uid
        
        # Generate code if becoming an execution project
        if vals.get('is_execution_project'):
            for project in self:
                if not project.national_project_code:
                    vals['national_project_code'] = self._generate_national_code(vals)
        
        return super().write(vals)

    def _generate_national_code(self, vals=None):
        """Generate unique national project code."""
        vals = vals or {}
        
        # Get project type code
        type_code = 'GEN'
        type_id = vals.get('execution_project_type_id') or self.execution_project_type_id.id
        if type_id:
            project_type = self.env['execution.project.type'].browse(type_id)
            type_code = project_type.code or 'GEN'
        
        # Get sector code
        sector_code = 'XX'
        sector_id = vals.get('execution_sector_id') or self.execution_sector_id.id
        if sector_id:
            sector = self.env['execution.sector'].browse(sector_id)
            sector_code = sector.code[:2] if sector.code else 'XX'
        
        # Get sequence number
        sequence = self.env['ir.sequence'].next_by_code('execution.project.code') or '0001'
        
        # Format: TYPE-SECTOR-YEAR-SEQUENCE
        year = date.today().strftime('%Y')
        return f'{type_code}-{sector_code}-{year}-{sequence}'

    # -------------------------------------------------------------------------
    # STATE TRANSITION ACTIONS
    # -------------------------------------------------------------------------
    def action_set_draft(self):
        """Reset project to draft state."""
        self._check_state_transition('draft')
        self.write({
            'execution_state': 'draft',
            'execution_state_reason': _('Reset to draft'),
        })

    def action_set_planned(self):
        """Move project to planned state."""
        self._check_state_transition('planned')
        for project in self:
            if not project.execution_planned_start or not project.execution_planned_end:
                raise UserError(
                    _('Please set planned start and end dates before planning the project.')
                )
            if not project.execution_budget:
                raise UserError(
                    _('Please set the project budget before planning.')
                )
        self.write({
            'execution_state': 'planned',
            'execution_state_reason': _('Project planned'),
        })

    def action_set_running(self):
        """Move project to running state."""
        self._check_state_transition('running')
        vals = {
            'execution_state': 'running',
            'execution_state_reason': _('Project execution started'),
        }
        for project in self:
            if not project.execution_actual_start:
                vals['execution_actual_start'] = date.today()
        self.write(vals)

    def action_set_at_risk(self):
        """Flag project as at risk."""
        self._check_state_transition('at_risk')
        return {
            'name': _('Set At Risk'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.project.state.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_new_state': 'at_risk',
            },
        }

    def action_set_suspended(self):
        """Suspend the project."""
        self._check_state_transition('suspended')
        return {
            'name': _('Suspend Project'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.project.state.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_new_state': 'suspended',
            },
        }

    def action_set_closed(self):
        """Close the project."""
        self._check_state_transition('closed')
        for project in self:
            if project.execution_progress < 100:
                raise UserError(
                    _('Cannot close project with progress less than 100%%. Current progress: %.2f%%') % project.execution_progress
                )
        vals = {
            'execution_state': 'closed',
            'execution_state_reason': _('Project completed and closed'),
        }
        for project in self:
            if not project.execution_actual_end:
                vals['execution_actual_end'] = date.today()
        self.write(vals)

    def action_resume_project(self):
        """Resume a suspended or at-risk project."""
        for project in self:
            if project.execution_state not in ('suspended', 'at_risk'):
                raise UserError(
                    _('Only suspended or at-risk projects can be resumed.')
                )
        self.write({
            'execution_state': 'running',
            'execution_state_reason': _('Project resumed'),
        })

    def _check_state_transition(self, new_state):
        """Validate state transitions."""
        allowed_transitions = {
            'draft': ['planned'],
            'planned': ['running', 'draft'],
            'running': ['at_risk', 'suspended', 'closed'],
            'at_risk': ['running', 'suspended', 'closed'],
            'suspended': ['running', 'closed'],
            'closed': [],  # Cannot transition from closed
        }
        
        for project in self:
            current = project.execution_state
            if new_state not in allowed_transitions.get(current, []) and new_state != current:
                # Allow going back to current state or validate transition
                if new_state == 'draft' and current != 'planned':
                    raise UserError(
                        _('Cannot transition from "%s" to "%s". '
                          'Allowed transitions: %s') % (
                            current, new_state,
                            ', '.join(allowed_transitions.get(current, ['None']))
                        )
                    )

    # -------------------------------------------------------------------------
    # REPORTING ACTIONS
    # -------------------------------------------------------------------------
    def action_view_progress_history(self):
        """View progress history for this project."""
        self.ensure_one()
        return {
            'name': _('Progress History'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.message',
            'view_mode': 'tree,form',
            'domain': [
                ('model', '=', 'project.project'),
                ('res_id', '=', self.id),
                ('tracking_value_ids.field_id.name', 'in', 
                 ['execution_progress', 'execution_physical_progress', 'execution_state']),
            ],
            'context': {'create': False, 'edit': False},
        }
