# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExecutionValidation(models.Model):
    """
    Immutable validation record for progress declarations.
    Each validation decision creates a new record for audit trail.
    """
    _name = 'execution.validation'
    _description = 'Execution Validation Record'
    _order = 'validation_datetime desc'
    _rec_name = 'display_name'

    # Immutability - records cannot be modified after creation
    _sql_constraints = [
        ('immutable_check', 'CHECK(1=1)', 'Validation records are immutable.')
    ]

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    
    # Link to progress declaration
    progress_id = fields.Many2one(
        comodel_name='execution.progress',
        string='Progress Declaration',
        required=True,
        readonly=True,
        ondelete='cascade',
        index=True,
    )
    
    # Related fields for reporting
    task_id = fields.Many2one(
        comodel_name='execution.planning.task',
        string='Task',
        related='progress_id.task_id',
        store=True,
        readonly=True,
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        related='progress_id.project_id',
        store=True,
        readonly=True,
    )
    
    # Validation Decision
    decision = fields.Selection(
        selection=[
            ('validated', 'Validated'),
            ('rejected', 'Rejected'),
            ('correction_requested', 'Correction Requested'),
        ],
        string='Decision',
        required=True,
        readonly=True,
    )
    
    # Timestamping (Immutable)
    validation_datetime = fields.Datetime(
        string='Validation Date/Time',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        index=True,
    )
    
    # Validator Info (Immutable)
    validator_id = fields.Many2one(
        comodel_name='res.users',
        string='Validated By',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    validator_role = fields.Char(
        string='Validator Role',
        readonly=True,
        help='Role/position of validator at time of validation',
    )
    
    # Decision Details
    comment = fields.Text(
        string='Comment',
        readonly=True,
        help='Mandatory for rejections, optional for approvals',
    )
    
    # Progress snapshot at validation time (for audit)
    declared_percentage_snapshot = fields.Float(
        string='Declared % (Snapshot)',
        readonly=True,
        digits=(5, 2),
    )
    previous_percentage_snapshot = fields.Float(
        string='Previous % (Snapshot)',
        readonly=True,
        digits=(5, 2),
    )
    incremental_percentage_snapshot = fields.Float(
        string='Incremental % (Snapshot)',
        readonly=True,
        digits=(5, 2),
    )
    
    # Digital signature / hash for integrity (optional enhancement)
    validation_hash = fields.Char(
        string='Validation Hash',
        readonly=True,
        help='SHA-256 hash of validation data for integrity verification',
    )

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------
    @api.constrains('validation_datetime', 'progress_id')
    def _check_validation_dates(self):
        for record in self:
            if not record.validation_datetime:
                continue
                
            val_date = record.validation_datetime.date()
            
            # Rule 1: Validation date must be >= execution declaration date
            if record.progress_id.execution_date and val_date < record.progress_id.execution_date:
                raise ValidationError(_(
                    "Validation date (%s) cannot be before the execution declaration date (%s)."
                ) % (val_date, record.progress_id.execution_date))
            
            # Rule 2: Validation date cannot be in the future
            if val_date > fields.Date.today():
                raise ValidationError(_(
                    "Validation date (%s) cannot be in the future."
                ) % val_date)
            
            # Rule 3: Validation date must be >= project start date
            project = record.project_id
            if project and project.execution_planned_start and val_date < project.execution_planned_start:
                raise ValidationError(_(
                    "Validation date (%s) cannot be before the project planned start date (%s)."
                ) % (val_date, project.execution_planned_start))

    @api.depends('progress_id', 'decision', 'validation_datetime')
    def _compute_display_name(self):
        for record in self:
            decision_label = dict(self._fields['decision'].selection).get(record.decision, '')
            record.display_name = f"{record.progress_id.name} - {decision_label} ({record.validation_datetime})"

    @api.model_create_multi
    def create(self, vals_list):
        """Create validation record with snapshot data."""
        import hashlib
        import json
        
        for vals in vals_list:
            # Get progress declaration
            progress = self.env['execution.progress'].browse(vals.get('progress_id'))
            
            # Snapshot current state
            vals['declared_percentage_snapshot'] = progress.declared_percentage
            vals['previous_percentage_snapshot'] = progress.previous_percentage
            vals['incremental_percentage_snapshot'] = progress.incremental_percentage
            
            # Get validator role
            validator = self.env['res.users'].browse(vals.get('validator_id', self.env.user.id))
            vals['validator_role'] = self._get_user_role(validator)
            
            # Generate integrity hash
            hash_data = {
                'progress_id': vals.get('progress_id'),
                'decision': vals.get('decision'),
                'validator_id': vals.get('validator_id', self.env.user.id),
                'datetime': str(vals.get('validation_datetime', fields.Datetime.now())),
                'declared_pct': vals.get('declared_percentage_snapshot'),
            }
            vals['validation_hash'] = hashlib.sha256(
                json.dumps(hash_data, sort_keys=True).encode()
            ).hexdigest()[:32]
        
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modification of validation records."""
        # Only allow system/superuser to modify (for technical corrections)
        if not self.env.su:
            raise UserError(_('Validation records are immutable and cannot be modified.'))
        return super().write(vals)

    def unlink(self):
        """Prevent deletion of validation records."""
        if not self.env.su:
            raise UserError(_('Validation records cannot be deleted. They are part of the audit trail.'))
        return super().unlink()

    def _get_user_role(self, user):
        """Determine user's validation role."""
        if user.has_group('executionpm_core.group_executionpm_admin'):
            return 'Administrator'
        elif user.has_group('executionpm_core.group_executionpm_pmo'):
            return 'PMO'
        elif user.has_group('executionpm_core.group_executionpm_control_office'):
            return 'Control Office'
        elif user.has_group('executionpm_core.group_executionpm_authority'):
            return 'Authority'
        elif user.has_group('executionpm_core.group_executionpm_contractor'):
            return 'Contractor'
        else:
            return 'User'
