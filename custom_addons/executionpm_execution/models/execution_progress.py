# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ExecutionProgress(models.Model):
    """
    Progress declaration submitted by contractors for a specific task.
    """
    _name = 'execution.progress'
    _description = 'Execution Progress Declaration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'execution_date desc, create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    
    # Linkage
    task_id = fields.Many2one(
        comodel_name='execution.planning.task',
        string='Task',
        required=True,
        tracking=True,
        domain="[('planning_id.state', '=', 'approved')]",
    )
    planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Planning',
        related='task_id.planning_id',
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        related='task_id.planning_id.project_id',
        store=True,
        readonly=True,
    )
    
    # Progress Data
    declared_percentage = fields.Float(
        string='Declared Progress (%)',
        required=True,
        tracking=True,
        digits=(5, 2),
        help='Cumulative percentage of task completion declared by contractor.',
    )
    previous_percentage = fields.Float(
        string='Previous Progress (%)',
        compute='_compute_previous_percentage',
        store=True,
        digits=(5, 2),
    )
    incremental_percentage = fields.Float(
        string='Incremental Progress (%)',
        compute='_compute_incremental_percentage',
        store=True,
        digits=(5, 2),
    )
    quantity_executed = fields.Float(
        string='Quantity Executed',
        tracking=True,
        help='Physical quantity executed (e.g., meters, cubic meters).',
    )
    quantity_unit = fields.Char(
        string='Unit',
        help='Unit of measurement for quantity.',
    )
    execution_date = fields.Date(
        string='Execution Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    comment = fields.Text(
        string='Comment / Description',
        required=True,
        help='Describe the work done.',
    )
    
    # Proof / Attachments
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='execution_progress_attachment_rel',
        column1='progress_id',
        column2='attachment_id',
        string='Proof Attachments',
    )
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count',
    )
    
    # Workflow
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
            ('validated', 'Validated'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    
    # Delay Tracking
    is_delayed = fields.Boolean(
        string='Is Delayed',
        compute='_compute_delay',
        store=True,
        help='True if execution date is after planned end date.',
    )
    delay_days = fields.Integer(
        string='Delay Days',
        compute='_compute_delay',
        store=True,
    )
    
    # Validation Info
    validated_by = fields.Many2one(
        comodel_name='res.users',
        string='Validated By',
        readonly=True,
        copy=False,
    )
    validated_date = fields.Date(
        string='Validation Date',
        readonly=True,
        copy=False,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('execution_date', 'task_id.date_end')
    def _compute_delay(self):
        for record in self:
            if record.execution_date and record.task_id.date_end:
                if record.execution_date > record.task_id.date_end:
                    delta = record.execution_date - record.task_id.date_end
                    record.is_delayed = True
                    record.delay_days = delta.days
                else:
                    record.is_delayed = False
                    record.delay_days = 0
            else:
                record.is_delayed = False
                record.delay_days = 0
    @api.depends('task_id')
    def _compute_previous_percentage(self):
        """Get the last validated percentage for this task."""
        for record in self:
            if record.task_id:
                last_validated = self.search([
                    ('task_id', '=', record.task_id.id),
                    ('state', '=', 'validated'),
                    ('id', '!=', record.id if record.id else 0),
                ], order='execution_date desc, id desc', limit=1)
                record.previous_percentage = last_validated.declared_percentage if last_validated else 0.0
            else:
                record.previous_percentage = 0.0

    @api.depends('declared_percentage', 'previous_percentage')
    def _compute_incremental_percentage(self):
        """Calculate the progress increment."""
        for record in self:
            record.incremental_percentage = record.declared_percentage - record.previous_percentage

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    @api.constrains('declared_percentage')
    def _check_declared_percentage(self):
        for record in self:
            if record.declared_percentage < 0 or record.declared_percentage > 100:
                raise ValidationError(_('Declared percentage must be between 0 and 100.'))
            if record.declared_percentage < record.previous_percentage:
                raise ValidationError(_(
                    'Declared percentage (%.2f%%) cannot be less than previous validated progress (%.2f%%).'
                ) % (record.declared_percentage, record.previous_percentage))
            
            # Rule: 100% progress cannot be declared before planned end date
            if (abs(record.declared_percentage - 100.0) < 0.01 and 
                    record.task_id.date_end and record.execution_date < record.task_id.date_end):
                raise ValidationError(_(
                    "You cannot declare 100%% completion for task '%s' before its planned end date (%s). "
                    "Current execution date: %s"
                ) % (record.task_id.name, record.task_id.date_end, record.execution_date))

    @api.constrains('execution_date', 'task_id')
    def _check_execution_date(self):
        for record in self:
            if not record.execution_date:
                continue

            # Rule 1: Cannot be in the future
            if record.execution_date > fields.Date.today():
                raise ValidationError(_(
                    "Execution date (%s) cannot be in the future."
                ) % record.execution_date)

            # Rule 2: Must be >= task planned start date
            if record.task_id and record.task_id.date_start and record.execution_date < record.task_id.date_start:
                raise ValidationError(_(
                    "Execution date (%s) cannot be before the task planned start date (%s)."
                ) % (record.execution_date, record.task_id.date_start))

            # Rule 3: Must be <= task planned end date
            if record.task_id and record.task_id.date_end and record.execution_date > record.task_id.date_end:
                raise ValidationError(_(
                    "Execution date (%s) cannot be after the task planned end date (%s)."
                ) % (record.execution_date, record.task_id.date_end))

            # Rule 4: Must be >= project start date
            project = record.project_id
            if project and project.execution_planned_start and record.execution_date < project.execution_planned_start:
                raise ValidationError(_(
                    "Execution date (%s) cannot be before the project planned start date (%s)."
                ) % (record.execution_date, project.execution_planned_start))

    @api.constrains('attachment_ids', 'state')
    def _check_attachments_on_submit(self):
        """Ensure attachments are present when submitting."""
        for record in self:
            if record.state == 'submitted' and not record.attachment_ids:
                raise ValidationError(_('At least one proof attachment is required before submitting.'))

    # -------------------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('execution.progress') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        # Prevent editing validated records (except by system/superuser)
        for record in self:
            if record.state == 'validated' and not self.env.su:
                # Allow only specific fields to be edited post-validation
                allowed_fields = {'message_follower_ids', 'message_ids', 'activity_ids'}
                if not set(vals.keys()).issubset(allowed_fields):
                    raise UserError(_('Validated progress declarations cannot be modified.'))
        return super().write(vals)

    # -------------------------------------------------------------------------
    # WORKFLOW ACTIONS
    # -------------------------------------------------------------------------
    def action_submit(self):
        """Submit declaration for review."""
        for record in self:
            if not record.attachment_ids:
                raise UserError(_('Please attach at least one proof document before submitting.'))
            if not record.comment:
                raise UserError(_('Please provide a comment describing the work done.'))
        self.write({'state': 'submitted'})

    def action_start_review(self):
        """Move to under review state."""
        self.write({'state': 'under_review'})

    def action_validate(self):
        """Validate the progress declaration and update task/project KPIs."""
        for record in self:
            if record.state != 'under_review':
                raise UserError(_('Only declarations under review can be validated.'))
            
            # Update the task's actual progress
            record.task_id.write({
                'actual_progress': record.declared_percentage,
            })
            
        self.write({
            'state': 'validated',
            'validated_by': self.env.user.id,
            'validated_date': fields.Date.today(),
            'rejection_reason': False,
        })
        
        # Post message to project
        for record in self:
            record.project_id.message_post(
                body=_('Progress validated for task "%s": %.2f%% (Declared by %s)') % (
                    record.task_id.name,
                    record.declared_percentage,
                    record.create_uid.name,
                ),
                message_type='notification',
            )

    def action_reject(self):
        """Open rejection wizard."""
        return {
            'name': _('Reject Progress Declaration'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.progress.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_progress_id': self.id},
        }

    def action_reset_draft(self):
        """Reset to draft for corrections."""
        for record in self:
            if record.state == 'validated':
                raise UserError(_('Validated declarations cannot be reset.'))
        self.write({'state': 'draft'})

    def action_view_attachments(self):
        """View all attachments."""
        self.ensure_one()
        return {
            'name': _('Proof Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }
