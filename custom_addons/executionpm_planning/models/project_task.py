# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectTask(models.Model):
    _inherit = 'project.task'

    execution_planning_task_id = fields.Many2one(
        comodel_name='execution.planning.task',
        string='Source Planning Task',
        readonly=True,
        ondelete='set null',
        help='The infrastructure planning task this Odoo task is synchronized with.'
    )

    execution_progress = fields.Float(
        string='Execution Progress (%)',
        readonly=True,
        digits=(5, 2),
        help='Progress synced from the infrastructure planning task.'
    )

    def write(self, vals):
        """
        Prevent manual status changes for synchronized tasks.
        The status should only change via the formal execution validation process.
        """
        if 'state' in vals and not self.env.context.get('sync_in_progress'):
            for task in self:
                if task.execution_planning_task_id:
                    raise ValidationError(_(
                        "Manual status changes are disabled for infrastructure tasks. \n\n"
                        "The status is automatically updated to 'Done' only when "
                        "validated progress reaches 100%."
                    ))
        return super().write(vals)

    def action_view_planning_task(self):
        """Open the linked execution planning task."""
        self.ensure_one()
        if not self.execution_planning_task_id:
            return
        return {
            'name': _('Planning Task'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.planning.task',
            'res_id': self.execution_planning_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
