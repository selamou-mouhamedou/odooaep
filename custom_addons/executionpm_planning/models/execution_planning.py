# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ExecutionPlanning(models.Model):
    """
    Master planning document for a project.
    Essentially the container for the Gantt chart data.
    """
    _name = 'execution.planning'
    _description = 'Execution Planning'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Planning Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        domain="[('is_execution_project', '=', True)]",
        tracking=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contractor',
        related='project_id.execution_contractor_id',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        required=True,
    )
    
    # Structure
    lot_ids = fields.One2many(
        comodel_name='execution.planning.lot',
        inverse_name='planning_id',
        string='Lots / Work Packages',
        tracking=True,
    )
    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_stats',
    )
    total_physical_weight = fields.Float(
        string='Total Physical Weight (%)',
        compute='_compute_task_stats',
        tracking=True,
        help='Sum of all task weights. Must be 100% for approval.',
    )
    
    # Dates
    planning_start_date = fields.Date(
        string='Planning Start',
        compute='_compute_date_range',
        store=True,
    )
    planning_end_date = fields.Date(
        string='Planning End',
        compute='_compute_date_range',
        store=True,
    )

    # Approver Info
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_date = fields.Date(string='Approval Date', readonly=True, copy=False)
    rejection_reason = fields.Text(string='Rejection Reason', copy=False)

    # Constraints
    _sql_constraints = [
        ('project_unique_active_planning', 
         'UNIQUE(project_id, active)', 
         'Only one active planning document is allowed per project! Archive old versions first.')
    ]
    
    active = fields.Boolean(default=True)

    @api.constrains('lot_ids', 'lot_ids.task_ids', 'lot_ids.task_ids.weight')
    def _check_total_weight(self):
        for record in self:
            if record.total_physical_weight > 100.001:  # Allow minimal float margin
                raise ValidationError(_(
                    "Total Physical Weight cannot surpass 100%%. Current total: %.2f%%.\n"
                    "Please adjust the weights of your tasks to stay within the 100%% limit."
                ) % record.total_physical_weight)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('execution.planning') or _('New')
        return super().create(vals_list)

    @api.depends('lot_ids.task_ids', 'lot_ids.task_ids.weight')
    def _compute_task_stats(self):
        for record in self:
            tasks = record.lot_ids.mapped('task_ids')
            record.task_count = len(tasks)
            record.total_physical_weight = sum(tasks.mapped('weight'))

    @api.depends('lot_ids.start_date', 'lot_ids.end_date')
    def _compute_date_range(self):
        for record in self:
            dates_start = [d for d in record.lot_ids.mapped('start_date') if d]
            dates_end = [d for d in record.lot_ids.mapped('end_date') if d]
            
            record.planning_start_date = min(dates_start) if dates_start else False
            record.planning_end_date = max(dates_end) if dates_end else False

    # Workflow Actions
    def action_submit(self):
        self.ensure_one()
        # Validation: Check weights
        if not abs(self.total_physical_weight - 100.0) < 0.01:
            raise ValidationError(_(
                "Total physical weight of tasks must be exactly 100%%. Current total: %.2f%%"
            ) % self.total_physical_weight)
            
        # Validation: Check dates within project limits? (Optional business rule)
        # Here just ensuring we have tasks
        if self.task_count == 0:
            raise ValidationError(_("You cannot submit an empty planning."))

        self.write({'state': 'submitted'})

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise ValidationError(_("Only submitted planning can be approved."))
            
        # Synchronize tasks to Odoo Project Tasks FIRST
        # We must do this before setting state to 'approved' because
        # once approved, record rules make planning tasks read-only for PMO.
        self._sync_to_project_tasks()

        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Date.today(),
            'rejection_reason': False
        })
        
        # Link this planning to the project as the master schedule
        self.project_id.message_post(
            body=_("New Execution Planning approved: %s") % self.name,
            message_type='notification'
        )


    def action_reject(self):
        return {
            'name': _('Reject Planning'),
            'type': 'ir.actions.act_window',
            'res_model': 'execution.planning.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_planning_id': self.id}
        }

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})

    def _sync_to_project_tasks(self):
        """
        Create or update Odoo project.task records for each planning task.
        Handles hierarchy (parent/subtasks).
        """
        self.ensure_one()
        ProjectTask = self.env['project.task']
        all_tasks = self.lot_ids.mapped('task_ids')
        
        # Pass 1: Create/Update tasks (base fields)
        for task in all_tasks:
            vals = {
                'name': task.name,
                'project_id': self.project_id.id,
                'planned_date_begin': task.date_start,
                'date_deadline': task.date_end,
                'sequence': task.sequence,
                'execution_planning_task_id': task.id,
                'state': '04_waiting_normal',
            }
            
            if task.project_task_id:
                task.project_task_id.write(vals)
            else:
                new_task = ProjectTask.create(vals)
                task.project_task_id = new_task.id

        # Pass 2: Setup Hierarchy
        for task in all_tasks:
            if task.parent_task_id and task.parent_task_id.project_task_id:
                task.project_task_id.parent_id = task.parent_task_id.project_task_id.id
            else:
                task.project_task_id.parent_id = False
