# -*- coding: utf-8 -*-
"""
Post-migration hook to reset dashboard board customizations.
This ensures the latest action domains from XML are applied.
"""

from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    """
    Hook called after module upgrade/installation.
    Clears any cached board customizations and forces action domains.
    """
    # 1. Force update the domain for our dashboard actions
    actions_to_update = [
        ('executionpm_execution.action_pmo_pending_validations', 
         "[('state', 'in', ['submitted', 'under_review', 'correction_requested'])]"),
        ('executionpm_execution.action_pmo_delayed_tasks',
         "[('date_end', '<', (context_today()).strftime('%Y-%m-%d')), ('progress_status', '!=', 'completed'), ('actual_progress', '<', 100)]"),
        ('executionpm_execution.action_contractor_active_tasks',
         "[('lot_id.planning_id.project_id.execution_contractor_id.related_user_id', '=', uid), ('progress_status', '!=', 'completed'), ('date_start', '<=', (context_today()).strftime('%Y-%m-%d')), ('date_end', '>=', (context_today()).strftime('%Y-%m-%d'))]"),
        ('executionpm_execution.action_contractor_delayed_tasks',
         "[('lot_id.planning_id.project_id.execution_contractor_id.related_user_id', '=', uid), ('progress_status', '!=', 'completed'), ('actual_progress', '<', 100), ('date_end', '<', (context_today()).strftime('%Y-%m-%d'))]"),
        ('executionpm_execution.action_contractor_rejected_declarations',
         "[('create_uid', '=', uid), ('state', 'in', ['rejected', 'correction_requested'])]"),
    ]
    
    for xml_id, domain in actions_to_update:
        try:
            action = env.ref(xml_id, raise_if_not_found=False)
            if action:
                action.domain = domain
        except Exception:
            pass

    # 2. Clear user customizations for the dashboards to force reload from XML
    dashboard_views = [
        'executionpm_execution.board_pmo_dashboard_final',
        'executionpm_execution.board_contractor_dashboard_final',
        'executionpm_core.board_authority_dashboard',
    ]
    for xml_id in dashboard_views:
        try:
            view = env.ref(xml_id, raise_if_not_found=False)
            if view:
                # Delete custom views for all users to force reload from XML
                env['ir.ui.view.custom'].search([('ref_id', '=', view.id)]).unlink()
        except Exception:
            pass

