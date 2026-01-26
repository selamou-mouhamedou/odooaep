# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    """
    Extend project with validation statistics.
    """
    _inherit = 'project.project'

    # Validation statistics
    total_validations = fields.Integer(
        string='Total Validations',
        compute='_compute_validation_stats',
    )
    pending_validations = fields.Integer(
        string='Pending Validations',
        compute='_compute_validation_stats',
    )

    @api.depends('planning_ids.lot_ids.task_ids.progress_declaration_ids.state')
    def _compute_validation_stats(self):
        for project in self:
            declarations = self.env['execution.progress'].search([
                ('project_id', '=', project.id)
            ])
            project.total_validations = len(declarations.filtered(lambda d: d.state == 'validated'))
            project.pending_validations = len(declarations.filtered(
                lambda d: d.state in ('submitted', 'under_review')
            ))

    def action_view_pending_validations(self):
        """View declarations pending validation for this project."""
        self.ensure_one()
        return {
            'name': _('Pending Validations'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.progress',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('state', 'in', ['submitted', 'under_review']),
            ],
            'context': {'search_default_to_review': 1},
        }

    # -------------------------------------------------------------------------
    # DATE CONSISTENCY CHECKS
    # -------------------------------------------------------------------------
    @api.constrains('execution_actual_start', 'execution_actual_end')
    def _check_actual_dates(self):
        """Rule: Project actual end date cannot be before actual start date."""
        for project in self:
            if (project.execution_actual_start and project.execution_actual_end and
                    project.execution_actual_end < project.execution_actual_start):
                raise ValidationError(_(
                    "Project '%s': Actual end date (%s) cannot be before actual start date (%s)."
                ) % (project.name, project.execution_actual_end, project.execution_actual_start))

    # -------------------------------------------------------------------------
    # STATE TRANSITION OVERRIDES
    # -------------------------------------------------------------------------
    def action_set_closed(self):
        """
        Rule: Project cannot be closed if:
        - tasks are incomplete (progress < 100%)
        - pending validations exist
        """
        for project in self:
            if project.is_execution_project:
                # 1. Check progress
                if project.execution_progress < 99.99:
                    raise UserError(_(
                        "Cannot close project '%s'! \n\n"
                        "All tasks must reach 100%% completion. Current progress: %.2f%%"
                    ) % (project.name, project.execution_progress))
                
                # 2. Check pending validations
                if project.pending_validations > 0:
                    raise UserError(_(
                        "Cannot close project '%s'! \n\n"
                        "There are %d pending progress declarations that must be validated or rejected."
                    ) % (project.name, project.pending_validations))

        return super().action_set_closed()
