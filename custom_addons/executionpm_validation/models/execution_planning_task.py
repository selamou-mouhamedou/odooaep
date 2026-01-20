# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExecutionPlanningTask(models.Model):
    """
    Extend planning task with validated progress tracking.
    """
    _inherit = 'execution.planning.task'

    # Validated progress count
    validated_declaration_count = fields.Integer(
        string='Validated Declarations',
        compute='_compute_validated_stats',
    )
    pending_declaration_count = fields.Integer(
        string='Pending Declarations',
        compute='_compute_validated_stats',
    )

    @api.depends('progress_declaration_ids.state')
    def _compute_validated_stats(self):
        for task in self:
            declarations = task.progress_declaration_ids
            task.validated_declaration_count = len(declarations.filtered(lambda d: d.state == 'validated'))
            task.pending_declaration_count = len(declarations.filtered(
                lambda d: d.state in ('submitted', 'under_review')
            ))
