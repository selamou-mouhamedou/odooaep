# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExecutionProgress(models.Model):
    """
    Extend progress declarations with formal validation workflow.
    """
    _inherit = 'execution.progress'

    # Override state to add 'correction_requested'
    state = fields.Selection(
        selection_add=[
            ('correction_requested', 'Correction Requested'),
        ],
        ondelete={'correction_requested': 'set default'},
    )
    
    # Link to validation records
    validation_ids = fields.One2many(
        comodel_name='execution.validation',
        inverse_name='progress_id',
        string='Validation History',
        readonly=True,
    )
    validation_count = fields.Integer(
        string='Validation Count',
        compute='_compute_validation_count',
    )
    
    # Latest validation info (for quick access)
    last_validation_id = fields.Many2one(
        comodel_name='execution.validation',
        string='Last Validation',
        compute='_compute_last_validation',
        store=True,
    )
    last_validation_decision = fields.Selection(
        related='last_validation_id.decision',
        string='Last Decision',
        store=True,
    )
    last_validator_id = fields.Many2one(
        related='last_validation_id.validator_id',
        string='Last Validator',
        store=True,
    )
    
    # Correction tracking
    correction_count = fields.Integer(
        string='Correction Rounds',
        default=0,
        readonly=True,
    )
    correction_comments = fields.Text(
        string='Correction Comments',
        readonly=True,
        help='Comments from validator requesting corrections',
    )

    @api.depends('validation_ids')
    def _compute_validation_count(self):
        for record in self:
            record.validation_count = len(record.validation_ids)

    @api.depends('validation_ids.validation_datetime')
    def _compute_last_validation(self):
        for record in self:
            last = record.validation_ids.sorted('validation_datetime', reverse=True)[:1]
            record.last_validation_id = last.id if last else False

    @api.constrains('validated_date', 'execution_date')
    def _check_validated_date(self):
        for record in self:
            if not record.validated_date:
                continue
            
            # Rule 1: Validation date must be >= execution declaration date
            if record.execution_date and record.validated_date < record.execution_date:
                raise ValidationError(_(
                    "The validation date (%s) cannot be before the execution date (%s)."
                ) % (record.validated_date, record.execution_date))
            
            # Rule 2: Validation date cannot be in the future
            if record.validated_date > fields.Date.today():
                raise ValidationError(_(
                    "The validation date (%s) cannot be in the future."
                ) % record.validated_date)
            
            # Rule 3: Validation date must be >= project start date
            project = record.project_id
            if project and project.execution_planned_start and record.validated_date < project.execution_planned_start:
                raise ValidationError(_(
                    "The validation date (%s) cannot be before the project planned start date (%s)."
                ) % (record.validated_date, project.execution_planned_start))

    # -------------------------------------------------------------------------
    # FORMAL VALIDATION ACTIONS (Override from execution module)
    # -------------------------------------------------------------------------
    def action_validate(self):
        """
        Formally validate the progress declaration.
        Creates immutable validation record and updates KPIs.
        """
        self.ensure_one()
        
        if self.state not in ('submitted', 'under_review'):
            raise UserError(_('Only submitted or under-review declarations can be validated.'))
        
        # Create immutable validation record
        self.env['execution.validation'].create({
            'progress_id': self.id,
            'decision': 'validated',
            'comment': _('Progress validated'),
        })
        
        # Update task's actual progress
        self.task_id.write({
            'actual_progress': self.declared_percentage,
        })
        
        # Update progress declaration state
        self.write({
            'state': 'validated',
            'validated_by': self.env.user.id,
            'validated_date': fields.Date.today(),
            'rejection_reason': False,
        })
        
        # Post to project chatter
        self.project_id.message_post(
            body=_('✓ Progress VALIDATED for task "%s": %.2f%% (Validated by %s)') % (
                self.task_id.name,
                self.declared_percentage,
                self.env.user.name,
            ),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        
        # Trigger project progress recalculation
        self._update_project_progress()
        
        return True

    def action_reject(self):
        """Open rejection wizard with mandatory comment."""
        self.ensure_one()
        return {
            'name': _('Reject Progress Declaration'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.validation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_progress_id': self.id,
                'default_action_type': 'reject',
            },
        }

    def action_request_correction(self):
        """Open correction request wizard with mandatory comment."""
        self.ensure_one()
        return {
            'name': _('Request Correction'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.validation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_progress_id': self.id,
                'default_action_type': 'correction',
            },
        }

    def action_view_validation_history(self):
        """View all validation records for this declaration."""
        self.ensure_one()
        return {
            'name': _('Validation History'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.validation',
            'view_mode': 'list,form',
            'domain': [('progress_id', '=', self.id)],
            'context': {'create': False, 'edit': False, 'delete': False},
        }

    def _do_reject(self, comment):
        """Execute rejection with validation record."""
        self.ensure_one()
        
        # Create immutable validation record
        self.env['execution.validation'].create({
            'progress_id': self.id,
            'decision': 'rejected',
            'comment': comment,
        })
        
        self.write({
            'state': 'rejected',
            'rejection_reason': comment,
        })
        
        # Notify declarant
        self.message_post(
            body=_('✗ Progress REJECTED by %s.\nReason: %s') % (self.env.user.name, comment),
            message_type='notification',
            partner_ids=[self.create_uid.partner_id.id],
        )

    def _do_request_correction(self, comment):
        """Execute correction request with validation record."""
        self.ensure_one()
        
        # Create immutable validation record
        self.env['execution.validation'].create({
            'progress_id': self.id,
            'decision': 'correction_requested',
            'comment': comment,
        })
        
        self.write({
            'state': 'correction_requested',
            'correction_comments': comment,
            'correction_count': self.correction_count + 1,
        })
        
        # Notify declarant
        self.message_post(
            body=_('⚠ CORRECTION REQUESTED by %s.\nComments: %s') % (self.env.user.name, comment),
            message_type='notification',
            partner_ids=[self.create_uid.partner_id.id],
        )

    def action_resubmit_after_correction(self):
        """Resubmit after making corrections."""
        self.ensure_one()
        if self.state != 'correction_requested':
            raise UserError(_('Can only resubmit declarations that need correction.'))
        
        if not self.attachment_ids:
            raise UserError(_('Please attach proof documents before resubmitting.'))
        
        self.write({
            'state': 'submitted',
            'correction_comments': False,
        })
        
        self.message_post(
            body=_('Declaration resubmitted after correction (Correction round %d)') % self.correction_count,
            message_type='notification',
        )

    def _update_project_progress(self):
        """Recalculate project overall progress based on validated task progress."""
        for record in self:
            project = record.project_id
            if not project or not project.is_execution_project:
                continue
            
            # Get all tasks from approved planning
            planning = project.active_planning_id
            if not planning:
                continue
            
            tasks = planning.lot_ids.mapped('task_ids')
            if not tasks:
                continue
            
            # Calculate weighted progress
            total_weight = sum(tasks.mapped('weight'))
            if total_weight <= 0:
                continue
            
            weighted_progress = sum(
                task.actual_progress * task.weight / total_weight
                for task in tasks
            )
            
            project_vals = {
                'execution_progress': weighted_progress,
                'execution_physical_progress': weighted_progress,
            }

            # Automation Rule: Set Actual Start at first validated execution
            validated_declarations = self.env['execution.progress'].search([
                ('project_id', '=', project.id),
                ('state', '=', 'validated')
            ])
            if validated_declarations:
                # Set start date to the earliest execution date of validated declarations
                if not project.execution_actual_start:
                    project_vals['execution_actual_start'] = min(validated_declarations.mapped('execution_date'))
                
                # Automation Rule: Set Actual End when all tasks reach 100%
                if weighted_progress >= 99.99: # Account for float precision
                    project_vals['execution_actual_end'] = max(validated_declarations.mapped('execution_date'))
            
            project.write(project_vals)
