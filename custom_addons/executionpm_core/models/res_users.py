from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Manual boolean fields that link to groups. 
    # This ensures we get Checkboxes in the UI that are always visible.
    
    group_executionpm_admin = fields.Boolean(
        string='Execution PM: Administrator',
        compute='_compute_executionpm_groups',
        inverse='_inverse_executionpm_admin',
        help="Full system access for Execution PM."
    )
    
    group_executionpm_pmo = fields.Boolean(
        string='Execution PM: PMO',
        compute='_compute_executionpm_groups',
        inverse='_inverse_executionpm_pmo',
        help="PMO access for validating declarations."
    )
    
    group_executionpm_control_office = fields.Boolean(
        string='Execution PM: Control Office',
        compute='_compute_executionpm_groups',
        inverse='_inverse_executionpm_control_office',
        help="Control Office access for reviewing declarations."
    )
    
    group_executionpm_contractor = fields.Boolean(
        string='Execution PM: Contractor',
        compute='_compute_executionpm_groups',
        inverse='_inverse_executionpm_contractor',
        help="Contractor access for declaring progress."
    )
    
    group_executionpm_authority = fields.Boolean(
        string='Execution PM: Authority',
        compute='_compute_executionpm_groups',
        inverse='_inverse_executionpm_authority',
        help="Read-only access across the board."
    )

    def _compute_executionpm_groups(self):
        for user in self:
            user.group_executionpm_admin = user.has_group('executionpm_core.group_executionpm_admin')
            user.group_executionpm_pmo = user.has_group('executionpm_core.group_executionpm_pmo')
            user.group_executionpm_control_office = user.has_group('executionpm_core.group_executionpm_control_office')
            user.group_executionpm_contractor = user.has_group('executionpm_core.group_executionpm_contractor')
            user.group_executionpm_authority = user.has_group('executionpm_core.group_executionpm_authority')

    def _inverse_executionpm_admin(self):
        self._set_group('executionpm_core.group_executionpm_admin', 'group_executionpm_admin')

    def _inverse_executionpm_pmo(self):
        self._set_group('executionpm_core.group_executionpm_pmo', 'group_executionpm_pmo')

    def _inverse_executionpm_control_office(self):
        self._set_group('executionpm_core.group_executionpm_control_office', 'group_executionpm_control_office')

    def _inverse_executionpm_contractor(self):
        self._set_group('executionpm_core.group_executionpm_contractor', 'group_executionpm_contractor')

    def _inverse_executionpm_authority(self):
        self._set_group('executionpm_core.group_executionpm_authority', 'group_executionpm_authority')

    def _set_group(self, group_xml_id, field_name):
        group = self.env.ref(group_xml_id)
        for user in self:
            if user[field_name]:
                user.write({'groups_id': [(4, group.id)]})
            else:
                user.write({'groups_id': [(3, group.id)]})
