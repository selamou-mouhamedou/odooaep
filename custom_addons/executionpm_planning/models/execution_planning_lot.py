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
    
    # Aggregates / Boundaries
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)

    @api.constrains('start_date', 'end_date', 'planning_id')
    def _check_lot_dates(self):
        for lot in self:
            if not lot.start_date or not lot.end_date:
                continue
                
            # Rule 1: Start < End
            if lot.start_date > lot.end_date:
                raise ValidationError(_(
                    "Lot '%s': Planned start date (%s) must be before planned end date (%s)."
                ) % (lot.name, lot.start_date, lot.end_date))
                
            project = lot.planning_id.project_id
            if project:
                # Rule 5: Lot dates must be inside project dates
                if project.execution_planned_start and lot.start_date < project.execution_planned_start:
                    raise ValidationError(_(
                        "Lot '%s': Start date (%s) cannot be before project planned start date (%s)."
                    ) % (lot.name, lot.start_date, project.execution_planned_start))
                    
                if project.execution_planned_end and lot.end_date > project.execution_planned_end:
                    raise ValidationError(_(
                        "Lot '%s': End date (%s) cannot be after project planned end date (%s)."
                    ) % (lot.name, lot.end_date, project.execution_planned_end))

            # Rule 4 (Inverse): All tasks must be within lot dates
            for task in lot.task_ids:
                if task.date_start and task.date_start < lot.start_date:
                    raise ValidationError(_(
                        "Lot '%s': Start date (%s) would exclude task '%s' which starts on %s."
                    ) % (lot.name, lot.start_date, task.name, task.date_start))
                
                if task.date_end and task.date_end > lot.end_date:
                    raise ValidationError(_(
                        "Lot '%s': End date (%s) would exclude task '%s' which ends on %s."
                    ) % (lot.name, lot.end_date, task.name, task.date_end))
