# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    execution_progress_id = fields.Many2one(
        'execution.progress',
        string='Linked Execution Progress',
        help="Link this invoice/bill to a specific execution progress declaration. "
             "Validation of the invoice requires the progress to be formally validated.",
        readonly=False,
        copy=False,
    )
    
    execution_project_id = fields.Many2one(
        'project.project',
        string='Execution Project',
        compute='_compute_execution_project',
        store=True,
        readonly=True,
    )

    def write(self, vals):
        # Prevent changing execution link after posting
        if 'execution_progress_id' in vals:
            for move in self:
                if move.state != 'draft':
                    raise UserError(_("You cannot modify the Execution Progress link on a posted entry."))
        return super(AccountMove, self).write(vals)

    @api.depends('execution_progress_id', 'execution_progress_id.project_id')
    def _compute_execution_project(self):
        for move in self:
            if move.execution_progress_id:
                move.execution_project_id = move.execution_progress_id.project_id
            else:
                # Optional: Try to infer from analytic accounts on lines if needed,
                # but for now we strictly respect the direct link or leave empty.
                move.execution_project_id = False

    def action_post(self):
        """
        Override action_post to block validation if linked progress is not validated.
        """
        for move in self:
            if move.execution_progress_id:
                # Check validation status
                if move.execution_progress_id.state != 'validated':
                    raise UserError(_(
                        "Validation Blocked: This entry is linked to Execution Progress '%s' "
                        "which has not been formally validated yet. Current status: %s.\n\n"
                        "Please ensure the progress declaration is validated before posting this financial record."
                    ) % (move.execution_progress_id.name, move.execution_progress_id.state))
        
        return super(AccountMove, self).action_post()
