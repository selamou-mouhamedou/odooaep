# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ExecutionValidationWizard(models.TransientModel):
    """
    Wizard for rejection and correction request actions.
    Ensures mandatory comment is provided.
    """
    _name = 'execution.validation.wizard'
    _description = 'Validation Action Wizard'

    progress_id = fields.Many2one(
        comodel_name='execution.progress',
        string='Progress Declaration',
        required=True,
        readonly=True,
    )
    action_type = fields.Selection(
        selection=[
            ('reject', 'Reject'),
            ('correction', 'Request Correction'),
        ],
        string='Action',
        required=True,
        readonly=True,
    )
    comment = fields.Text(
        string='Comment',
        required=True,
        help='This comment is mandatory and will be visible to the contractor.',
    )

    def action_confirm(self):
        """Execute the validation action."""
        self.ensure_one()
        
        if not self.comment or len(self.comment.strip()) < 10:
            raise UserError(_('Please provide a meaningful comment (at least 10 characters).'))
        
        if self.action_type == 'reject':
            self.progress_id._do_reject(self.comment)
        elif self.action_type == 'correction':
            self.progress_id._do_request_correction(self.comment)
        
        return {'type': 'ir.actions.act_window_close'}
