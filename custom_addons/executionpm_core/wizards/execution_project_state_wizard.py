# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ExecutionProjectStateWizard(models.TransientModel):
    _name = 'execution.project.state.wizard'
    _description = 'Project State Change Wizard'

    project_id = fields.Many2one(
        'project.project', 
        string='Project', 
        required=True,
    )
    new_state = fields.Selection([
        ('at_risk', 'At Risk'),
        ('suspended', 'Suspended'),
    ], string='New State', required=True)
    
    reason = fields.Text(
        string='Reason', 
        required=True,
        help='Summarize why this project state is changing.'
    )

    def action_confirm(self):
        self.ensure_one()
        if not self.reason or len(self.reason.strip()) < 5:
            raise UserError(_("Please provide a valid reason (minimum 5 characters)."))
            
        self.project_id.write({
            'execution_state': self.new_state,
            'execution_state_reason': self.reason,
        })
        return {'type': 'ir.actions.act_window_close'}
