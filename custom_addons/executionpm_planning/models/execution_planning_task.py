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

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start > record.date_end:
                raise ValidationError(_("End date cannot be earlier than start date for task: %s") % record.name)
