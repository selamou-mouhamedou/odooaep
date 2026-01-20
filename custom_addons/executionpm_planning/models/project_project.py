# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    planning_ids = fields.One2many(
        comodel_name='execution.planning',
        inverse_name='project_id',
        string='Planning Documents',
    )
    
    active_planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Active Planning',
        compute='_compute_active_planning',
        store=True,
    )
    
    planning_count = fields.Integer(compute='_compute_planning_count')

    @api.depends('planning_ids')
    def _compute_planning_count(self):
        for project in self:
            project.planning_count = len(project.planning_ids)

    def action_view_planning(self):
        self.ensure_one()
        return {
            'name': _('Execution Planning'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.planning',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    @api.depends('planning_ids.state')
    def _compute_active_planning(self):
        for project in self:
            # Get the latest approved planning
            approved = project.planning_ids.filtered(lambda p: p.state == 'approved')
            project.active_planning_id = approved[:1] if approved else False

    def action_set_running(self):
        """Override to enforce planning requirement."""
        for project in self:
            if project.is_execution_project:
                if not project.active_planning_id:
                    raise ValidationError(_(
                        "Cannot start execution! \n\n"
                        "An approved Execution Planning document is required before moving to the Running state."
                    ))
        return super().action_set_running()
