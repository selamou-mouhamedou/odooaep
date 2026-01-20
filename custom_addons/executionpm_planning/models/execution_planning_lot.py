# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ExecutionPlanningLot(models.Model):
    """
    Subdivision of planning (e.g., "Civil Works", "Electrical", "Lot 1").
    Groups tasks together.
    """
    _name = 'execution.planning.lot'
    _description = 'Planning Lot / Work Package'
    _order = 'sequence, id'

    name = fields.Char(string='Lot / Package Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Planning Reference',
        required=True,
        ondelete='cascade',
    )
    
    task_ids = fields.One2many(
        comodel_name='execution.planning.task',
        inverse_name='lot_id',
        string='Tasks',
    )
    
    # Aggregates
    start_date = fields.Date(compute='_compute_lot_dates', store=True)
    end_date = fields.Date(compute='_compute_lot_dates', store=True)

    @api.depends('task_ids.date_start', 'task_ids.date_end')
    def _compute_lot_dates(self):
        for record in self:
            starts = [d for d in record.task_ids.mapped('date_start') if d]
            ends = [d for d in record.task_ids.mapped('date_end') if d]
            record.start_date = min(starts) if starts else False
            record.end_date = max(ends) if ends else False
