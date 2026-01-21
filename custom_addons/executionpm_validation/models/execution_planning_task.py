# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExecutionPlanningTask(models.Model):
    """
    Extend planning task with validated progress tracking.
    """
    _inherit = 'execution.planning.task'

    # Validated progress count is inherited from executionpm_execution
    
    pending_declaration_count = fields.Integer(
        string='Pending Declarations',
        compute='_compute_pending_stats',
    )

    @api.depends('progress_declaration_ids.state')
    def _compute_pending_stats(self):
        for task in self:
            declarations = task.progress_declaration_ids
            task.pending_declaration_count = len(declarations.filtered(
                lambda d: d.state in ('submitted', 'under_review')
            ))
