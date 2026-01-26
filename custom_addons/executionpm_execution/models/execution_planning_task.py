# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ExecutionPlanningTask(models.Model):
    """
    Extend planning task to track actual progress from validated declarations.
    """
    _inherit = 'execution.planning.task'

    # Actual Progress (updated when declarations are validated)
    actual_progress = fields.Float(
        string='Actual Progress (%)',
        default=0.0,
        tracking=True,
        digits=(5, 2),
        help='Current validated progress percentage.',
    )
    
    # Link to declarations
    progress_declaration_ids = fields.One2many(
        comodel_name='execution.progress',
        inverse_name='task_id',
        string='Progress Declarations',
    )
    progress_declaration_count = fields.Integer(
        string='Declarations',
        compute='_compute_progress_declaration_count',
    )
    
    # Computed progress status
    progress_status = fields.Selection(
        selection=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
        ],
        string='Progress Status',
        compute='_compute_progress_status',
        store=True,
    )
    
    # Delay Info
    is_delayed = fields.Boolean(
        string='Is Delayed',
        compute='_compute_task_delay',
        store=True,
        help='True if any validated or submitted declaration for this task is delayed.',
    )
    max_delay_days = fields.Integer(
        string='Max Delay (Days)',
        compute='_compute_task_delay',
        store=True,
    )

    @api.depends('progress_declaration_ids.is_delayed', 'progress_declaration_ids.delay_days', 'progress_declaration_ids.state')
    def _compute_task_delay(self):
        for task in self:
            # We consider a task delayed if any of its progress declarations (submitted or validated) are delayed
            declarations = task.progress_declaration_ids.filtered(lambda d: d.state in ('submitted', 'validated'))
            delayed_decls = declarations.filtered(lambda d: d.is_delayed)
            task.is_delayed = bool(delayed_decls)
            task.max_delay_days = max(delayed_decls.mapped('delay_days')) if delayed_decls else 0

    @api.depends('progress_declaration_ids')
    def _compute_progress_declaration_count(self):
        for task in self:
            task.progress_declaration_count = len(task.progress_declaration_ids)

    @api.depends('actual_progress')
    def _compute_progress_status(self):
        for task in self:
            if task.actual_progress >= 100:
                task.progress_status = 'completed'
            elif task.actual_progress > 0:
                task.progress_status = 'in_progress'
            else:
                task.progress_status = 'not_started'

    def action_view_declarations(self):
        """View progress declarations for this task."""
        self.ensure_one()
        return {
            'name': _('Progress Declarations'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.progress',
            'view_mode': 'list,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }

    def action_new_declaration(self):
        """Quick action to create new declaration."""
        self.ensure_one()
        return {
            'name': _('New Progress Declaration'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.progress',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_task_id': self.id,
            },
        }
