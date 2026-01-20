# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


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
