# -*- coding: utf-8 -*-
"""
Execution Alert Model

Manages alerts for execution projects with severity levels, 
automatic status tracking, and notification capabilities.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta


class ExecutionAlert(models.Model):
    """
    Alert model for tracking project execution issues.
    """
    _name = 'execution.alert'
    _description = 'Execution Project Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, create_date desc'
    _rec_name = 'display_name'

    # -------------------------------------------------------------------------
    # ALERT IDENTIFICATION
    # -------------------------------------------------------------------------
    name = fields.Char(
        string='Alert Reference',
        readonly=True,
        copy=False,
        default='New',
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    
    # -------------------------------------------------------------------------
    # ALERT TYPE & SEVERITY
    # -------------------------------------------------------------------------
    alert_type = fields.Selection([
        ('delay', 'Task Delay'),
        ('not_started_delay', 'Task Not Started'),
        ('inactivity', 'No Activity'),
        ('inconsistency', 'Progress Inconsistency'),
        ('budget', 'Budget Alert'),
        ('custom', 'Custom Alert'),
    ], string='Alert Type', required=True, tracking=True)
    
    severity = fields.Selection([
        ('1_low', 'Low'),
        ('2_medium', 'Medium'),
        ('3_high', 'High'),
        ('4_critical', 'Critical'),
    ], string='Severity', required=True, default='2_medium', tracking=True)
    
    state = fields.Selection([
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ], string='Status', default='open', required=True, tracking=True)

    # -------------------------------------------------------------------------
    # RELATED RECORDS
    # -------------------------------------------------------------------------
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[('is_execution_project', '=', True)]",
    )
    planning_id = fields.Many2one(
        comodel_name='execution.planning',
        string='Planning',
        ondelete='set null',
    )
    task_id = fields.Many2one(
        comodel_name='execution.planning.task',
        string='Task',
        ondelete='set null',
    )
    progress_declaration_id = fields.Many2one(
        comodel_name='execution.progress',
        string='Progress Declaration',
        ondelete='set null',
    )

    # -------------------------------------------------------------------------
    # ALERT DETAILS
    # -------------------------------------------------------------------------
    title = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    description = fields.Html(
        string='Description',
        help='Detailed description of the alert condition.',
    )
    
    # Threshold values (for reference)
    threshold_value = fields.Float(
        string='Threshold Value',
        help='The threshold value that was exceeded.',
    )
    actual_value = fields.Float(
        string='Actual Value',
        help='The actual value that triggered the alert.',
    )
    deviation = fields.Float(
        string='Deviation',
        compute='_compute_deviation',
        store=True,
    )
    unit = fields.Char(
        string='Unit',
        help='Unit of measurement (days, %, etc.)',
    )

    # -------------------------------------------------------------------------
    # DATES & ASSIGNMENT
    # -------------------------------------------------------------------------
    alert_date = fields.Date(
        string='Alert Date',
        default=fields.Date.today,
        required=True,
    )
    due_date = fields.Date(
        string='Due Date',
        help='Deadline to address this alert.',
    )
    acknowledged_date = fields.Datetime(
        string='Acknowledged Date',
    )
    acknowledged_by = fields.Many2one(
        comodel_name='res.users',
        string='Acknowledged By',
    )
    resolved_date = fields.Datetime(
        string='Resolved Date',
    )
    resolved_by = fields.Many2one(
        comodel_name='res.users',
        string='Resolved By',
    )
    assigned_to = fields.Many2one(
        comodel_name='res.users',
        string='Assigned To',
        tracking=True,
    )
    
    # -------------------------------------------------------------------------
    # RESOLUTION
    # -------------------------------------------------------------------------
    resolution_notes = fields.Html(
        string='Resolution Notes',
    )
    action_taken = fields.Text(
        string='Action Taken',
    )

    # -------------------------------------------------------------------------
    # NOTIFICATION FLAGS
    # -------------------------------------------------------------------------
    notification_sent = fields.Boolean(
        string='Notification Sent',
        default=False,
    )
    reminder_count = fields.Integer(
        string='Reminder Count',
        default=0,
    )
    last_reminder_date = fields.Date(
        string='Last Reminder Date',
    )

    # -------------------------------------------------------------------------
    # COMPUTED FIELDS
    # -------------------------------------------------------------------------
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True,
    )
    days_open = fields.Integer(
        string='Days Open',
        compute='_compute_days_open',
    )
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('name', 'title', 'project_id.name')
    def _compute_display_name(self):
        for alert in self:
            if alert.name and alert.name != 'New':
                alert.display_name = f"[{alert.name}] {alert.title or ''}"
            else:
                alert.display_name = alert.title or 'New Alert'

    @api.depends('threshold_value', 'actual_value')
    def _compute_deviation(self):
        for alert in self:
            alert.deviation = alert.actual_value - alert.threshold_value

    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        today = date.today()
        for alert in self:
            if alert.state in ('resolved', 'dismissed'):
                alert.is_overdue = False
            elif alert.due_date:
                alert.is_overdue = alert.due_date < today
            else:
                alert.is_overdue = False

    @api.depends('alert_date')
    def _compute_days_open(self):
        today = date.today()
        for alert in self:
            if alert.alert_date:
                alert.days_open = (today - alert.alert_date).days
            else:
                alert.days_open = 0

    @api.depends('severity', 'state')
    def _compute_color(self):
        """Color coding based on severity and state."""
        for alert in self:
            if alert.state in ('resolved', 'dismissed'):
                alert.color = 10  # Green
            elif alert.severity == '4_critical':
                alert.color = 1  # Red
            elif alert.severity == '3_high':
                alert.color = 2  # Orange
            elif alert.severity == '2_medium':
                alert.color = 3  # Yellow
            else:
                alert.color = 4  # Light blue

    # -------------------------------------------------------------------------
    # CRUD OVERRIDE
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('execution.alert') or 'New'
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------
    def action_acknowledge(self):
        """Mark alert as acknowledged."""
        self.write({
            'state': 'acknowledged',
            'acknowledged_date': fields.Datetime.now(),
            'acknowledged_by': self.env.uid,
        })
        return True

    def action_start_progress(self):
        """Mark alert as in progress."""
        self.write({'state': 'in_progress'})
        return True

    def action_resolve(self):
        """Mark alert as resolved."""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.uid,
        })
        return True

    def action_dismiss(self):
        """Dismiss the alert."""
        self.write({'state': 'dismissed'})
        return True

    def action_reopen(self):
        """Reopen a resolved or dismissed alert."""
        self.write({
            'state': 'open',
            'resolved_date': False,
            'resolved_by': False,
        })
        return True

    def action_send_notification(self):
        """Send notification email for this alert."""
        self.ensure_one()
        template = self.env.ref('executionpm_alerts.mail_template_execution_alert', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.write({
                'notification_sent': True,
                'reminder_count': self.reminder_count + 1,
                'last_reminder_date': date.today(),
            })
        return True

    def action_view_project(self):
        """Open related project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_task(self):
        """Open related task."""
        self.ensure_one()
        if not self.task_id:
            raise UserError(_('No task associated with this alert.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'execution.planning.task',
            'res_id': self.task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # ALERT GENERATION METHODS (Called by Cron)
    # -------------------------------------------------------------------------
    @api.model
    def _cron_check_task_delays(self):
        """
        Cron job: Check for task delays exceeding threshold.
        Creates alerts for tasks that are behind schedule.
        """
        config = self.env['execution.alert.config'].get_config()
        if not config.delay_alert_enabled:
            return
        
        threshold_days = config.delay_threshold_days
        today = date.today()
        
        # Find tasks that should have ended but haven't reached 100%
        tasks = self.env['execution.planning.task'].search([
            ('planning_id.state', '=', 'approved'),
            ('date_end', '<', today),
            ('validated_progress', '<', 100),
        ])
        
        for task in tasks:
            delay_days = (today - task.date_end).days
            
            if delay_days >= threshold_days:
                # Check if alert already exists for this task
                existing = self.search([
                    ('task_id', '=', task.id),
                    ('alert_type', '=', 'delay'),
                    ('state', 'not in', ['resolved', 'dismissed']),
                ], limit=1)
                
                if not existing:
                    severity = self._get_delay_severity(delay_days, config)
                    self._create_delay_alert(task, delay_days, severity, config)

    @api.model
    def _cron_check_not_started(self):
        """
        Cron job: Check for tasks that haven't started after planned start date.
        """
        config = self.env['execution.alert.config'].get_config()
        if not config.not_started_alert_enabled:
            return
            
        threshold_days = config.not_started_threshold_days
        today = date.today()
        
        # Find tasks that should have started but have 0% progress
        tasks = self.env['execution.planning.task'].search([
            ('planning_id.state', '=', 'approved'),
            ('date_start', '<', today),
            ('validated_progress', '=', 0),
        ])
        
        for task in tasks:
            days_after_start = (today - task.date_start).days
            
            if days_after_start >= threshold_days:
                # Check if alert already exists
                existing = self.search([
                    ('task_id', '=', task.id),
                    ('alert_type', '=', 'not_started_delay'),
                    ('state', 'not in', ['resolved', 'dismissed']),
                ], limit=1)
                
                if not existing:
                    self._create_not_started_alert(task, days_after_start, config)

    @api.model
    def _cron_check_overdue(self):
        """
        Cron job: Check for tasks that are past their end date (Overdue).
        This is a variant of delay check, specifically emphasizing the Overdue status.
        """
        # This is already partially handled by _cron_check_task_delays.
        # However, we can use it to specifically target tasks past deadline.
        self._cron_check_task_delays()

    @api.model
    def _cron_check_inactivity(self):
        """
        Cron job: Check for projects with no execution updates for X days.
        """
        config = self.env['execution.alert.config'].get_config()
        if not config.inactivity_alert_enabled:
            return
        
        inactivity_days = config.inactivity_threshold_days
        threshold_date = date.today() - timedelta(days=inactivity_days)
        
        # Find running projects
        projects = self.env['project.project'].search([
            ('is_execution_project', '=', True),
            ('execution_state', '=', 'running'),
        ])
        
        for project in projects:
            # Check last progress declaration date
            last_progress = self.env['execution.progress'].search([
                ('project_id', '=', project.id),
            ], order='execution_date desc', limit=1)
            
            last_activity_date = last_progress.execution_date if last_progress else project.execution_actual_start
            
            if last_activity_date and last_activity_date < threshold_date:
                # Check if alert already exists
                existing = self.search([
                    ('project_id', '=', project.id),
                    ('alert_type', '=', 'inactivity'),
                    ('state', 'not in', ['resolved', 'dismissed']),
                ], limit=1)
                
                if not existing:
                    days_inactive = (date.today() - last_activity_date).days
                    self._create_inactivity_alert(project, days_inactive, last_activity_date, config)

    @api.model
    def _cron_check_progress_inconsistency(self):
        """
        Cron job: Check for progress inconsistencies between declared and planned.
        """
        config = self.env['execution.alert.config'].get_config()
        if not config.inconsistency_alert_enabled:
            return
        
        threshold_percent = config.inconsistency_threshold_percent
        
        # Find tasks with significant deviation
        tasks = self.env['execution.planning.task'].search([
            ('planning_id.state', '=', 'approved'),
            ('validated_progress', '>', 0),  # Has some progress
        ])
        
        for task in tasks:
            # Check deviation
            deviation = abs(task.progress_deviation)
            
            if deviation >= threshold_percent:
                # Check if alert already exists
                existing = self.search([
                    ('task_id', '=', task.id),
                    ('alert_type', '=', 'inconsistency'),
                    ('state', 'not in', ['resolved', 'dismissed']),
                ], limit=1)
                
                if not existing:
                    severity = self._get_inconsistency_severity(deviation, config)
                    self._create_inconsistency_alert(task, deviation, severity, config)

    @api.model
    def _cron_send_alert_reminders(self):
        """
        Cron job: Send reminders for unresolved alerts.
        """
        config = self.env['execution.alert.config'].get_config()
        if not config.reminder_enabled:
            return
        
        reminder_interval = config.reminder_interval_days
        threshold_date = date.today() - timedelta(days=reminder_interval)
        
        alerts = self.search([
            ('state', 'in', ['open', 'acknowledged', 'in_progress']),
            '|',
            ('last_reminder_date', '=', False),
            ('last_reminder_date', '<=', threshold_date),
            ('reminder_count', '<', config.max_reminders),
        ])
        
        for alert in alerts:
            alert.action_send_notification()

    # -------------------------------------------------------------------------
    # HELPER METHODS
    # -------------------------------------------------------------------------
    def _get_delay_severity(self, delay_days, config):
        """Determine severity based on delay days."""
        if delay_days >= config.critical_delay_days:
            return '4_critical'
        elif delay_days >= config.high_delay_days:
            return '3_high'
        elif delay_days >= config.medium_delay_days:
            return '2_medium'
        return '1_low'

    def _get_inconsistency_severity(self, deviation, config):
        """Determine severity based on progress deviation."""
        if deviation >= config.critical_inconsistency_percent:
            return '4_critical'
        elif deviation >= config.high_inconsistency_percent:
            return '3_high'
        elif deviation >= config.medium_inconsistency_percent:
            return '2_medium'
        return '1_low'

    def _create_delay_alert(self, task, delay_days, severity, config):
        """Create a task delay alert."""
        project = task.planning_id.project_id
        
        description = f"""
        <p><strong>Task Delay Alert</strong></p>
        <ul>
            <li><strong>Task:</strong> {task.name}</li>
            <li><strong>Planning:</strong> {task.planning_id.name}</li>
            <li><strong>Planned End Date:</strong> {task.date_end}</li>
            <li><strong>Days Delayed:</strong> {delay_days} days</li>
            <li><strong>Current Progress:</strong> {task.validated_progress:.1f}%</li>
        </ul>
        <p>This task has exceeded the acceptable delay threshold of {config.delay_threshold_days} days.</p>
        """
        
        alert = self.create({
            'alert_type': 'delay',
            'severity': severity,
            'project_id': project.id,
            'planning_id': task.planning_id.id,
            'task_id': task.id,
            'title': f"Task Delay: {task.name}",
            'description': description,
            'threshold_value': config.delay_threshold_days,
            'actual_value': delay_days,
            'unit': 'days',
            'assigned_to': project.user_id.id if project.user_id else False,
            'due_date': date.today() + timedelta(days=config.default_due_days),
        })
        
        if config.auto_notify:
            alert.action_send_notification()
        
        return alert

    def _create_inactivity_alert(self, project, days_inactive, last_activity_date, config):
        """Create an inactivity alert."""
        description = f"""
        <p><strong>Project Inactivity Alert</strong></p>
        <ul>
            <li><strong>Project:</strong> {project.name}</li>
            <li><strong>Last Activity:</strong> {last_activity_date}</li>
            <li><strong>Days Inactive:</strong> {days_inactive} days</li>
            <li><strong>Current Progress:</strong> {project.execution_physical_progress:.1f}%</li>
        </ul>
        <p>No execution updates have been recorded for this project in the last {days_inactive} days.</p>
        """
        
        severity = '3_high' if days_inactive > config.inactivity_threshold_days * 2 else '2_medium'
        
        alert = self.create({
            'alert_type': 'inactivity',
            'severity': severity,
            'project_id': project.id,
            'title': f"No Activity: {project.name}",
            'description': description,
            'threshold_value': config.inactivity_threshold_days,
            'actual_value': days_inactive,
            'unit': 'days',
            'assigned_to': project.user_id.id if project.user_id else False,
            'due_date': date.today() + timedelta(days=config.default_due_days),
        })
        
        if config.auto_notify:
            alert.action_send_notification()
        
        return alert

    def _create_inconsistency_alert(self, task, deviation, severity, config):
        """Create a progress inconsistency alert."""
        project = task.planning_id.project_id
        
        status = "behind" if task.progress_deviation < 0 else "ahead of"
        
        description = f"""
        <p><strong>Progress Inconsistency Alert</strong></p>
        <ul>
            <li><strong>Task:</strong> {task.name}</li>
            <li><strong>Planning:</strong> {task.planning_id.name}</li>
            <li><strong>Planned Progress:</strong> {task.planned_progress_to_date:.1f}%</li>
            <li><strong>Actual Progress:</strong> {task.validated_progress:.1f}%</li>
            <li><strong>Deviation:</strong> {task.progress_deviation:+.1f}%</li>
        </ul>
        <p>This task is {abs(deviation):.1f}% {status} schedule, exceeding the threshold of {config.inconsistency_threshold_percent}%.</p>
        """
        
        alert = self.create({
            'alert_type': 'inconsistency',
            'severity': severity,
            'project_id': project.id,
            'planning_id': task.planning_id.id,
            'task_id': task.id,
            'title': f"Progress Deviation: {task.name}",
            'description': description,
            'threshold_value': config.inconsistency_threshold_percent,
            'actual_value': deviation,
            'unit': '%',
            'assigned_to': project.user_id.id if project.user_id else False,
            'due_date': date.today() + timedelta(days=config.default_due_days),
        })
        
        if config.auto_notify:
            alert.action_send_notification()
        
        return alert

    def _create_not_started_alert(self, task, days_after_start, config):
        """Create a 'Task Not Started' alert."""
        project = task.planning_id.project_id
        
        description = f"""
        <p><strong>Task Not Started Alert</strong></p>
        <ul>
            <li><strong>Task:</strong> {task.name}</li>
            <li><strong>Planning:</strong> {task.planning_id.name}</li>
            <li><strong>Planned Start Date:</strong> {task.date_start}</li>
            <li><strong>Days Overdue for Start:</strong> {days_after_start} days</li>
        </ul>
        <p>This task has not recorded any progress despite being {days_after_start} days past its planned start date.</p>
        """
        
        severity = '2_medium' if days_after_start < 7 else '3_high'
        
        alert = self.create({
            'alert_type': 'not_started_delay',
            'severity': severity,
            'project_id': project.id,
            'planning_id': task.planning_id.id,
            'task_id': task.id,
            'title': f"Not Started: {task.name}",
            'description': description,
            'threshold_value': config.not_started_threshold_days,
            'actual_value': days_after_start,
            'unit': 'days',
            'assigned_to': project.user_id.id if project.user_id else False,
            'due_date': date.today() + timedelta(days=config.default_due_days),
        })
        
        if config.auto_notify:
            alert.action_send_notification()
            
        return alert
