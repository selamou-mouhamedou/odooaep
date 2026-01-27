# -*- coding: utf-8 -*-
"""
Progress Computation Module

Computes:
- Task actual progress (validated only)
- Project global progress (weighted average)
- Planned vs actual curve data

All computations use only validated execution data and are automatically triggered.
"""
from odoo import api, fields, models, _
from datetime import date, timedelta
import json


class ExecutionPlanningTaskProgress(models.Model):
    """
    Extend planning task to compute actual progress from validated declarations only.
    """
    _inherit = 'execution.planning.task'

    # -------------------------------------------------------------------------
    # COMPUTED PROGRESS FIELDS (Validated Only)
    # -------------------------------------------------------------------------
    validated_progress = fields.Float(
        string='Validated Progress (%)',
        compute='_compute_validated_progress',
        store=True,
        digits=(5, 2),
        help='Progress from validated declarations only.',
    )
    validated_declaration_count = fields.Integer(
        string='Validated Declarations',
        compute='_compute_validated_progress',
        store=True,
    )
    last_validated_date = fields.Date(
        string='Last Validation Date',
        compute='_compute_validated_progress',
        store=True,
    )
    
    # Progress deviation
    progress_deviation = fields.Float(
        string='Progress Deviation (%)',
        compute='_compute_progress_deviation',
        store=True,
        digits=(5, 2),
        help='Difference between planned and actual progress. Negative means behind schedule.',
    )
    planned_progress_to_date = fields.Float(
        string='Planned Progress to Date (%)',
        compute='_compute_planned_progress_to_date',
        digits=(5, 2),
        help='Expected progress percentage based on timeline.',
    )
    
    # Weighted contribution to project
    weighted_contribution = fields.Float(
        string='Weighted Contribution (%)',
        compute='_compute_weighted_contribution',
        store=True,
        digits=(5, 4),
        help='This task\'s contribution to overall project progress.',
    )

    # -------------------------------------------------------------------------
    # COMPUTE: Validated Progress (Triggered by declaration state changes)
    # -------------------------------------------------------------------------
    @api.depends('progress_declaration_ids.state', 'progress_declaration_ids.declared_percentage')
    def _compute_validated_progress(self):
        """
        Compute actual progress from validated declarations only.
        Uses optimized batch query to minimize database calls.
        """
        if not self:
            return

        # Batch query: Get all validated declarations for all tasks in one query
        validated_declarations = self.env['execution.progress'].search([
            ('task_id', 'in', self.ids),
            ('state', '=', 'validated'),
        ], order='task_id, execution_date desc, id desc')

        # Group by task_id for O(1) lookup
        task_declarations = {}
        for decl in validated_declarations:
            task_id = decl.task_id.id
            if task_id not in task_declarations:
                task_declarations[task_id] = []
            task_declarations[task_id].append(decl)

        for task in self:
            declarations = task_declarations.get(task.id, [])
            task.validated_declaration_count = len(declarations)
            
            if declarations:
                # First in list is the latest (due to ordering)
                latest = declarations[0]
                task.validated_progress = latest.declared_percentage
                task.last_validated_date = latest.validated_date or latest.execution_date
            else:
                task.validated_progress = 0.0
                task.last_validated_date = False

        # Sync progress to Odoo Project Tasks
        for task in self:
            if task.project_task_id:
                # Sync to our custom field on the project task
                vals = {'execution_progress': task.validated_progress}
                if task.validated_progress >= 100:
                    vals['state'] = '1_done'
                elif task.validated_progress > 0:
                    vals['state'] = '01_in_progress'
                else:
                    vals['state'] = '04_waiting_normal'
                task.project_task_id.with_context(sync_in_progress=True).write(vals)

    # -------------------------------------------------------------------------
    # COMPUTE: Planned Progress to Date (Time-based)
    # -------------------------------------------------------------------------
    @api.depends('date_start', 'date_end', 'duration')
    def _compute_planned_progress_to_date(self):
        """
        Calculate expected progress based on linear interpolation of timeline.
        """
        today = date.today()
        for task in self:
            if not task.date_start or not task.date_end:
                task.planned_progress_to_date = 0.0
                continue
                
            if today < task.date_start:
                task.planned_progress_to_date = 0.0
            elif today >= task.date_end:
                task.planned_progress_to_date = 100.0
            else:
                # Linear interpolation
                total_days = (task.date_end - task.date_start).days or 1
                elapsed_days = (today - task.date_start).days
                task.planned_progress_to_date = min(100.0, (elapsed_days / total_days) * 100)

    # -------------------------------------------------------------------------
    # COMPUTE: Progress Deviation
    # -------------------------------------------------------------------------
    @api.depends('validated_progress', 'planned_progress_to_date')
    def _compute_progress_deviation(self):
        """
        Calculate deviation: positive = ahead, negative = behind schedule.
        """
        for task in self:
            task.progress_deviation = task.validated_progress - task.planned_progress_to_date

    # -------------------------------------------------------------------------
    # COMPUTE: Weighted Contribution to Project
    # -------------------------------------------------------------------------
    @api.depends('validated_progress', 'weight')
    def _compute_weighted_contribution(self):
        """
        Calculate this task's weighted contribution to overall project progress.
        weighted_contribution = (validated_progress / 100) * weight
        """
        for task in self:
            task.weighted_contribution = (task.validated_progress / 100.0) * task.weight if task.weight else 0.0


class ExecutionPlanningProgress(models.Model):
    """
    Extend planning to compute overall progress from tasks.
    """
    _inherit = 'execution.planning'

    # -------------------------------------------------------------------------
    # OVERALL PLANNING PROGRESS
    # -------------------------------------------------------------------------
    overall_validated_progress = fields.Float(
        string='Overall Progress (%)',
        compute='_compute_overall_progress',
        store=True,
        digits=(5, 2),
        help='Weighted average progress from all validated task declarations.',
    )
    tasks_completed_count = fields.Integer(
        string='Completed Tasks',
        compute='_compute_overall_progress',
        store=True,
    )
    tasks_in_progress_count = fields.Integer(
        string='Tasks In Progress',
        compute='_compute_overall_progress',
        store=True,
    )
    tasks_not_started_count = fields.Integer(
        string='Tasks Not Started',
        compute='_compute_overall_progress',
        store=True,
    )

    # -------------------------------------------------------------------------
    # COMPUTE: Overall Progress (Weighted Average)
    # -------------------------------------------------------------------------
    @api.depends(
        'lot_ids.task_ids.validated_progress',
        'lot_ids.task_ids.weight',
        'lot_ids.task_ids.weighted_contribution'
    )
    def _compute_overall_progress(self):
        """
        Compute weighted average progress across all tasks.
        Formula: SUM(task.validated_progress * task.weight) / SUM(task.weight)
        
        This is equivalent to: SUM(task.weighted_contribution)
        since weighted_contribution = (validated_progress/100) * weight
        and SUM(weights) = 100%
        """
        for planning in self:
            tasks = planning.lot_ids.mapped('task_ids')
            
            if not tasks:
                planning.overall_validated_progress = 0.0
                planning.tasks_completed_count = 0
                planning.tasks_in_progress_count = 0
                planning.tasks_not_started_count = 0
                continue

            # Sum weighted contributions (already computed per task)
            total_weighted = sum(tasks.mapped('weighted_contribution'))
            planning.overall_validated_progress = total_weighted

            # Count by status
            planning.tasks_completed_count = len(tasks.filtered(lambda t: t.validated_progress >= 100))
            planning.tasks_in_progress_count = len(tasks.filtered(lambda t: 0 < t.validated_progress < 100))
            planning.tasks_not_started_count = len(tasks.filtered(lambda t: t.validated_progress == 0))


class ProjectProjectProgress(models.Model):
    """
    Extend project to compute global progress from approved planning.
    """
    _inherit = 'project.project'

    # -------------------------------------------------------------------------
    # PROJECT GLOBAL PROGRESS (from approved planning)
    # -------------------------------------------------------------------------
    computed_physical_progress = fields.Float(
        string='Computed Physical Progress (%)',
        compute='_compute_project_progress',
        store=True,
        digits=(5, 2),
        help='Weighted average of validated task progress from approved planning.',
    )
    active_planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Active Planning',
        compute='_compute_active_planning',
        store=True,
    )
    progress_last_updated = fields.Datetime(
        string='Progress Last Updated',
        compute='_compute_project_progress',
        store=True,
    )
    
    # Curve data for charting (stored as JSON)
    planned_curve_data = fields.Text(
        string='Planned S-Curve Data',
        compute='_compute_curve_data',
        help='JSON data for planned progress curve.',
    )
    actual_curve_data = fields.Text(
        string='Actual S-Curve Data',
        compute='_compute_curve_data',
        help='JSON data for actual progress curve.',
    )

    # -------------------------------------------------------------------------
    # COMPUTE: Active Planning
    # -------------------------------------------------------------------------
    @api.depends('is_execution_project')
    def _compute_active_planning(self):
        """Find the active approved planning for each project."""
        for project in self:
            if project.is_execution_project:
                planning = self.env['execution.planning'].search([
                    ('project_id', '=', project.id),
                    ('state', '=', 'approved'),
                    ('active', '=', True),
                ], limit=1, order='approved_date desc')
                project.active_planning_id = planning.id if planning else False
            else:
                project.active_planning_id = False

    # -------------------------------------------------------------------------
    # COMPUTE: Project Global Progress (Weighted Average from Planning)
    # -------------------------------------------------------------------------
    @api.depends('active_planning_id.overall_validated_progress')
    def _compute_project_progress(self):
        """
        Compute project's physical progress from the active planning.
        Also sync to the execution_physical_progress field.
        """
        for project in self:
            if project.active_planning_id:
                progress = project.active_planning_id.overall_validated_progress
                project.computed_physical_progress = progress
                project.progress_last_updated = fields.Datetime.now()
            else:
                project.computed_physical_progress = 0.0
                project.progress_last_updated = False

    # -------------------------------------------------------------------------
    # COMPUTE: S-Curve Data (Planned vs Actual)
    # -------------------------------------------------------------------------
    @api.depends('active_planning_id', 'active_planning_id.lot_ids.task_ids')
    def _compute_curve_data(self):
        """
        Generate planned vs actual curve data for charting.
        Returns JSON data suitable for rendering S-curves.
        """
        for project in self:
            if not project.active_planning_id:
                project.planned_curve_data = json.dumps([])
                project.actual_curve_data = json.dumps([])
                continue

            planning = project.active_planning_id
            tasks = planning.lot_ids.mapped('task_ids')
            
            if not tasks:
                project.planned_curve_data = json.dumps([])
                project.actual_curve_data = json.dumps([])
                continue

            # Get date range
            start_dates = [t.date_start for t in tasks if t.date_start]
            end_dates = [t.date_end for t in tasks if t.date_end]
            
            if not start_dates or not end_dates:
                project.planned_curve_data = json.dumps([])
                project.actual_curve_data = json.dumps([])
                continue

            project_start = min(start_dates)
            project_end = max(end_dates)
            
            # Generate planned curve (cumulative weight by end date)
            planned_curve = project._generate_planned_curve(tasks, project_start, project_end)
            project.planned_curve_data = json.dumps(planned_curve)
            
            # Generate actual curve (cumulative validated progress by validation date)
            actual_curve = project._generate_actual_curve(tasks, project_start)
            project.actual_curve_data = json.dumps(actual_curve)

    def _generate_planned_curve(self, tasks, project_start, project_end):
        """
        Generate planned S-curve data.
        Each point represents cumulative planned progress at a given date.
        """
        curve_data = []
        total_days = (project_end - project_start).days + 1
        
        # Sample at weekly intervals for performance
        interval_days = max(1, total_days // 52)  # Max 52 data points
        
        current_date = project_start
        while current_date <= project_end:
            # Calculate expected progress at this date
            cumulative_planned = 0.0
            
            for task in tasks:
                if not task.date_start or not task.date_end:
                    continue
                    
                if current_date < task.date_start:
                    # Task not started yet
                    task_progress = 0.0
                elif current_date >= task.date_end:
                    # Task should be complete
                    task_progress = 100.0
                else:
                    # Linear interpolation
                    task_days = (task.date_end - task.date_start).days or 1
                    elapsed = (current_date - task.date_start).days
                    task_progress = (elapsed / task_days) * 100
                
                # Add weighted contribution
                cumulative_planned += (task_progress / 100.0) * task.weight
            
            curve_data.append({
                'date': current_date.isoformat(),
                'progress': round(cumulative_planned, 2),
            })
            
            current_date += timedelta(days=interval_days)
        
        # Ensure we include the end date
        if curve_data and curve_data[-1]['date'] != project_end.isoformat():
            curve_data.append({
                'date': project_end.isoformat(),
                'progress': 100.0,
            })
        
        return curve_data

    def _generate_actual_curve(self, tasks, project_start):
        """
        Generate actual S-curve data from validated declarations.
        Each point represents cumulative actual progress at validation date.
        """
        # Get all validated declarations for these tasks
        declarations = self.env['execution.progress'].search([
            ('task_id', 'in', tasks.ids),
            ('state', '=', 'validated'),
        ], order='validated_date asc, id asc')
        
        if not declarations:
            return []
        
        curve_data = []
        task_progress_map = {task.id: 0.0 for task in tasks}
        task_weight_map = {task.id: task.weight for task in tasks}
        
        # Start point
        curve_data.append({
            'date': project_start.isoformat(),
            'progress': 0.0,
        })
        
        # Process each declaration in chronological order
        last_date = None
        for decl in declarations:
            validation_date = decl.validated_date or decl.execution_date
            if not validation_date:
                continue
                
            # Update task progress
            task_progress_map[decl.task_id.id] = decl.declared_percentage
            
            # Calculate cumulative weighted progress
            cumulative = sum(
                (progress / 100.0) * task_weight_map.get(task_id, 0)
                for task_id, progress in task_progress_map.items()
            )
            
            # Only add point if date changed (avoid duplicate dates)
            if validation_date != last_date:
                curve_data.append({
                    'date': validation_date.isoformat(),
                    'progress': round(cumulative, 2),
                })
                last_date = validation_date
            else:
                # Update last point with new cumulative value
                if curve_data:
                    curve_data[-1]['progress'] = round(cumulative, 2)
        
        # Add current date point if has progress
        today = date.today()
        if curve_data and last_date and today > last_date:
            curve_data.append({
                'date': today.isoformat(),
                'progress': curve_data[-1]['progress'],
            })
        
        return curve_data

    # -------------------------------------------------------------------------
    # ACTION: Refresh Progress Computation
    # -------------------------------------------------------------------------
    def action_refresh_progress(self):
        """
        Manually trigger progress recomputation.
        Useful for dashboard refresh buttons.
        """
        self.ensure_one()
        
        # Recompute planning first
        if self.active_planning_id:
            tasks = self.active_planning_id.lot_ids.mapped('task_ids')
            tasks._compute_validated_progress()
            self.active_planning_id._compute_overall_progress()
        
        # Recompute project
        self._compute_project_progress()
        self._compute_curve_data()
        
        # Sync to legacy field
        self.execution_physical_progress = self.computed_physical_progress
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Progress Updated'),
                'message': _('Physical progress: %.2f%%') % self.computed_physical_progress,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_scurve(self):
        """
        Open S-Curve visualization.
        """
        self.ensure_one()
        return {
            'name': _('S-Curve Analysis'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_ref': 'executionpm_execution.view_project_scurve_form'},
        }


class ExecutionProgressTrigger(models.Model):
    """
    Extend execution.progress to trigger recomputation on validation.
    """
    _inherit = 'execution.progress'

    def action_validate(self):
        """
        Override to ensure progress fields are recomputed after validation.
        """
        result = super().action_validate()
        
        # Trigger recomputation on related records
        # (The @api.depends should handle this, but we force it for reliability)
        tasks = self.mapped('task_id')
        if tasks:
            # Invalidate cache to force recomputation
            tasks.invalidate_recordset(['validated_progress', 'weighted_contribution'])
            
            # Trigger project-level recomputation
            projects = tasks.mapped('planning_id.project_id')
            projects.invalidate_recordset(['computed_physical_progress'])
        
        return result
