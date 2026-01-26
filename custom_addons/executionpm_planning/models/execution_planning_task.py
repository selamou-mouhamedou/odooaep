# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ExecutionPlanningTask(models.Model):
    """
    Granular planning task.
    """
    _name = 'execution.planning.task'
    _description = 'Planning Task'
    _order = 'lot_id, sequence, date_start'

    name = fields.Char(string='Task Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    lot_id = fields.Many2one(
        comodel_name='execution.planning.lot',
        string='Lot / Package',
        required=True,
        ondelete='cascade',
    )
    planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Planning Reference',
        related='lot_id.planning_id',
        store=True,
        readonly=True,
    )
    parent_task_id = fields.Many2one(
        comodel_name='execution.planning.task',
        string='Parent Task',
        domain="[('lot_id', '=', lot_id)]",
        ondelete='cascade',
    )
    subtask_ids = fields.One2many(
        comodel_name='execution.planning.task',
        inverse_name='parent_task_id',
        string='Subtasks',
    )

    # Timeline
    date_start = fields.Date(string='Planned Start', required=True)
    date_end = fields.Date(string='Planned End', required=True)
    duration = fields.Integer(string='Duration (Days)', compute='_compute_duration', store=True)

    # Weighting
    weight = fields.Float(
        string='Physical Weight (%)',
        required=True,
        default=0.0,
        digits=(5, 3), # Allow 3 decimals for precision (e.g. 0.125%)
        help='Contribution of this task to the overall 100% project progress.'
    )

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.duration = delta.days + 1  # Inclusive
            else:
                record.duration = 0

    @api.constrains('date_start', 'date_end', 'lot_id')
    def _check_task_dates(self):
        for task in self:
            if not task.date_start or not task.date_end:
                continue

            # Rule 1: Start < End
            if task.date_start > task.date_end:
                raise ValidationError(_(
                    "Task '%s': Planned start date (%s) must be before planned end date (%s)."
                ) % (task.name, task.date_start, task.date_end))

            project = task.planning_id.project_id
            if project:
                # Rule 2: Start cannot be before project start
                if project.execution_planned_start and task.date_start < project.execution_planned_start:
                    raise ValidationError(_(
                        "Task '%s': Start date (%s) cannot be before project planned start date (%s)."
                    ) % (task.name, task.date_start, project.execution_planned_start))
                
                # Rule 3: End cannot be after project end
                if project.execution_planned_end and task.date_end > project.execution_planned_end:
                    raise ValidationError(_(
                        "Task '%s': End date (%s) cannot be after project planned end date (%s)."
                    ) % (task.name, task.date_end, project.execution_planned_end))

            # Rule 4: Task inside parent lot
            if task.lot_id:
                if task.lot_id.start_date and task.date_start < task.lot_id.start_date:
                    raise ValidationError(_(
                        "Task '%s': Start date (%s) cannot be before lot start date (%s)."
                    ) % (task.name, task.date_start, task.lot_id.start_date))
                
                if task.lot_id.end_date and task.date_end > task.lot_id.end_date:
                    raise ValidationError(_(
                        "Task '%s': End date (%s) cannot be after lot end date (%s)."
                    ) % (task.name, task.date_end, task.lot_id.end_date))
