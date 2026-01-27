# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProjectTask(models.Model):
    _inherit = 'project.task'

    execution_progress_status = fields.Selection(
        related='execution_planning_task_id.progress_status',
        string='Execution Status',
        store=True,
    )
