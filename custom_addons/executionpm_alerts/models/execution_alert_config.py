# -*- coding: utf-8 -*-
"""
Alert Configuration Model

Centralized configuration for alert thresholds and notification settings.
"""
from odoo import api, fields, models, _


class ExecutionAlertConfig(models.Model):
    """
    Singleton configuration model for alert settings.
    """
    _name = 'execution.alert.config'
    _description = 'Execution Alert Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string='Configuration Name',
        default='Default Alert Configuration',
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # -------------------------------------------------------------------------
    # DELAY ALERT SETTINGS
    # -------------------------------------------------------------------------
    delay_alert_enabled = fields.Boolean(
        string='Enable Delay Alerts',
        default=True,
        help='Generate alerts when tasks exceed the delay threshold.',
    )
    delay_threshold_days = fields.Integer(
        string='Delay Threshold (Days)',
        default=3,
        help='Minimum days of delay before generating an alert.',
    )
    # Severity thresholds for delay
    medium_delay_days = fields.Integer(
        string='Medium Severity (Days)',
        default=3,
        help='Days of delay for medium severity.',
    )
    high_delay_days = fields.Integer(
        string='High Severity (Days)',
        default=7,
        help='Days of delay for high severity.',
    )
    critical_delay_days = fields.Integer(
        string='Critical Severity (Days)',
        default=14,
        help='Days of delay for critical severity.',
    )

    # -------------------------------------------------------------------------
    # NOT STARTED ALERT SETTINGS
    # -------------------------------------------------------------------------
    not_started_alert_enabled = fields.Boolean(
        string='Enable Not Started Alerts',
        default=True,
        help='Generate alerts when tasks have not started after their planned start date.',
    )
    not_started_threshold_days = fields.Integer(
        string='Not Started Threshold (Days)',
        default=3,
        help='Minimum days after planned start before generating an alert.',
    )

    # -------------------------------------------------------------------------
    # INACTIVITY ALERT SETTINGS
    # -------------------------------------------------------------------------
    inactivity_alert_enabled = fields.Boolean(
        string='Enable Inactivity Alerts',
        default=True,
        help='Generate alerts when no updates are recorded for a project.',
    )
    inactivity_threshold_days = fields.Integer(
        string='Inactivity Threshold (Days)',
        default=7,
        help='Days without updates before generating an alert.',
    )

    # -------------------------------------------------------------------------
    # INCONSISTENCY ALERT SETTINGS
    # -------------------------------------------------------------------------
    inconsistency_alert_enabled = fields.Boolean(
        string='Enable Inconsistency Alerts',
        default=True,
        help='Generate alerts when progress deviates significantly from plan.',
    )
    inconsistency_threshold_percent = fields.Float(
        string='Inconsistency Threshold (%)',
        default=15.0,
        help='Minimum deviation percentage before generating an alert.',
    )
    # Severity thresholds for inconsistency
    medium_inconsistency_percent = fields.Float(
        string='Medium Severity (%)',
        default=15.0,
        help='Deviation percentage for medium severity.',
    )
    high_inconsistency_percent = fields.Float(
        string='High Severity (%)',
        default=25.0,
        help='Deviation percentage for high severity.',
    )
    critical_inconsistency_percent = fields.Float(
        string='Critical Severity (%)',
        default=40.0,
        help='Deviation percentage for critical severity.',
    )

    # -------------------------------------------------------------------------
    # NOTIFICATION SETTINGS
    # -------------------------------------------------------------------------
    auto_notify = fields.Boolean(
        string='Auto Notify',
        default=True,
        help='Automatically send notifications when alerts are created.',
    )
    reminder_enabled = fields.Boolean(
        string='Enable Reminders',
        default=True,
        help='Send reminder notifications for unresolved alerts.',
    )
    reminder_interval_days = fields.Integer(
        string='Reminder Interval (Days)',
        default=3,
        help='Days between reminder notifications.',
    )
    max_reminders = fields.Integer(
        string='Max Reminders',
        default=5,
        help='Maximum number of reminder notifications to send.',
    )
    default_due_days = fields.Integer(
        string='Default Due Days',
        default=7,
        help='Default number of days to set alert due date.',
    )

    # -------------------------------------------------------------------------
    # NOTIFICATION RECIPIENTS
    # -------------------------------------------------------------------------
    notify_project_manager = fields.Boolean(
        string='Notify Project Manager',
        default=True,
    )
    notify_users = fields.Many2many(
        comodel_name='res.users',
        relation='execution_alert_config_user_rel',
        column1='config_id',
        column2='user_id',
        string='Additional Recipients',
        help='Additional users to receive alert notifications.',
    )
    notify_groups = fields.Many2many(
        comodel_name='res.groups',
        relation='execution_alert_config_group_rel',
        column1='config_id',
        column2='group_id',
        string='Notify Groups',
        help='User groups to receive alert notifications.',
    )

    # -------------------------------------------------------------------------
    # METHODS
    # -------------------------------------------------------------------------
    @api.model
    def get_config(self):
        """
        Get the active configuration for the current company.
        Creates a default one if none exists.
        """
        config = self.search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True),
        ], limit=1)
        
        if not config:
            config = self.create({
                'name': f'Alert Configuration - {self.env.company.name}',
                'company_id': self.env.company.id,
            })
        
        return config

    def action_test_delay_check(self):
        """Test button to run delay check manually."""
        self.env['execution.alert']._cron_check_task_delays()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Completed'),
                'message': _('Delay check completed.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_inactivity_check(self):
        """Test button to run inactivity check manually."""
        self.env['execution.alert']._cron_check_inactivity()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Completed'),
                'message': _('Inactivity check completed.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_inconsistency_check(self):
        """Test button to run inconsistency check manually."""
        self.env['execution.alert']._cron_check_progress_inconsistency()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Completed'),
                'message': _('Inconsistency check completed.'),
                'type': 'success',
                'sticky': False,
            }
        }
