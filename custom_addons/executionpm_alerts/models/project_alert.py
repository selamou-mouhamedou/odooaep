# -*- coding: utf-8 -*-
"""
Project Alert Extension

Extends project.project to show alert counts and provide quick access to alerts.
"""
from odoo import api, fields, models


class ProjectProjectAlert(models.Model):
    """
    Extend project to show associated alerts.
    """
    _inherit = 'project.project'

    # -------------------------------------------------------------------------
    # ALERT RELATIONSHIP
    # -------------------------------------------------------------------------
    alert_ids = fields.One2many(
        comodel_name='execution.alert',
        inverse_name='project_id',
        string='Alerts',
    )
    
    # -------------------------------------------------------------------------
    # ALERT COUNTS
    # -------------------------------------------------------------------------
    alert_count = fields.Integer(
        string='Alerts',
        compute='_compute_alert_counts',
    )
    open_alert_count = fields.Integer(
        string='Open Alerts',
        compute='_compute_alert_counts',
    )
    critical_alert_count = fields.Integer(
        string='Critical Alerts',
        compute='_compute_alert_counts',
    )
    has_critical_alerts = fields.Boolean(
        string='Has Critical Alerts',
        compute='_compute_alert_counts',
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('alert_ids', 'alert_ids.state', 'alert_ids.severity')
    def _compute_alert_counts(self):
        for project in self:
            alerts = project.alert_ids
            project.alert_count = len(alerts)
            project.open_alert_count = len(alerts.filtered(
                lambda a: a.state in ('open', 'acknowledged', 'in_progress')
            ))
            critical_alerts = alerts.filtered(
                lambda a: a.severity == '4_critical' and a.state not in ('resolved', 'dismissed')
            )
            project.critical_alert_count = len(critical_alerts)
            project.has_critical_alerts = project.critical_alert_count > 0

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------
    def action_view_alerts(self):
        """Open alerts view for this project."""
        self.ensure_one()
        return {
            'name': f'Alerts - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'execution.alert',
            'view_mode': 'list,form,kanban',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'search_default_filter_open': 1,
            },
        }

    def action_view_open_alerts(self):
        """Open only open alerts for this project."""
        self.ensure_one()
        return {
            'name': f'Open Alerts - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'execution.alert',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('state', 'in', ['open', 'acknowledged', 'in_progress']),
            ],
            'context': {
                'default_project_id': self.id,
            },
        }

    def action_view_critical_alerts(self):
        """Open only critical alerts for this project."""
        self.ensure_one()
        return {
            'name': f'Critical Alerts - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'execution.alert',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('severity', '=', '4_critical'),
                ('state', 'not in', ['resolved', 'dismissed']),
            ],
            'context': {
                'default_project_id': self.id,
                'default_severity': '4_critical',
            },
        }
