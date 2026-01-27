import sys
sys.path.append('/Users/selamou/Desktop/odoo18-project/odoo')
import odoo
from odoo import api, SUPERUSER_ID

def fix_security_links():
    odoo.tools.config.parse_config(['-c', '/Users/selamou/Desktop/odoo18-project/odoo.conf'])
    db_name = 'odoo18'
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # 1. Clean up broken view that prevents _update_user_groups_view() from running
        broken_view = env['ir.ui.view'].search([('name', '=', 'res.users.view.form.inherit.executionpm')])
        if broken_view:
            print("Deleting old/broken inherited user view to allow repair...")
            broken_view.unlink()
            
        # 2. Define the expected hierarchy
        hierarchy = {
            'group_executionpm_base': ['base.group_user'],
            'group_executionpm_contractor': ['executionpm_core.group_executionpm_base'],
            'group_executionpm_control_office': ['executionpm_core.group_executionpm_base'],
            'group_executionpm_pmo': ['executionpm_core.group_executionpm_control_office'],
            'group_executionpm_authority': ['executionpm_core.group_executionpm_base'],
            'group_executionpm_admin': ['executionpm_core.group_executionpm_pmo', 'executionpm_core.group_executionpm_authority'],
        }
        
        for group_xml_id, implied_xml_ids in hierarchy.items():
            group = env.ref(f'executionpm_core.{group_xml_id}', raise_if_not_found=False)
            if not group:
                print(f"Warning: Group {group_xml_id} not found!")
                continue
                
            implied_groups = []
            for i_xml_id in implied_xml_ids:
                i_group = env.ref(i_xml_id, raise_if_not_found=False)
                if i_group:
                    implied_groups.append(i_group.id)
                else:
                    print(f"Warning: Implied group {i_xml_id} not found for {group_xml_id}!")
            
            if implied_groups:
                print(f"Syncing implied groups for {group_xml_id}: {implied_xml_ids}")
                group.write({'implied_ids': [(6, 0, implied_groups)]})
        
        # 3. Recompute for all users
        print("Triggering group recomputation for all users...")
        users = env['res.users'].search([('active', '=', True)])
        for user in users:
            user.write({'groups_id': [(4, g.id) for g in user.groups_id]})
            
        cr.commit()
        print("Security links fixed and users updated.")

if __name__ == "__main__":
    fix_security_links()
