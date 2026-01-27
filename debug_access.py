import sys
sys.path.append('/Users/selamou/Desktop/odoo18-project/odoo')
import odoo
from odoo import api, SUPERUSER_ID

def debug_access():
    odoo.tools.config.parse_config(['-c', '/Users/selamou/Desktop/odoo18-project/odoo.conf'])
    db_name = 'odoo18'
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env['res.users'].browse(8)
        attachment = env['ir.attachment'].browse(887)
        
        print(f"Debugging User: {user.name} (ID: {user.id})")
        print(f"Debugging Attachment: {attachment.name} (ID: {attachment.id})")
        
        # Test read as user
        try:
            attachment.with_user(user).read(['name'])
            print("SUCCESS: User can read the attachment.")
        except Exception as e:
            print(f"FAILED: User cannot read the attachment. Error: {e}")
            
        # Check specific rules
        print("\n--- Checking Record Rules for ir.attachment ---")
        rules = env['ir.rule'].search([('model_id.model', '=', 'ir.attachment'), ('active', '=', True)])
        for rule in rules:
            print(f"Rule: {rule.name}")
            print(f"  Domain: {rule.domain_force}")
            print(f"  Global: {getattr(rule, 'global')}")
            print(f"  Groups: {[g.full_name for g in rule.groups]}")
            
            # Check if user matches rule groups
            user_groups = user.groups_id.ids
            matching_groups = [g.id for g in rule.groups if g.id in user_groups]
            if matching_groups or not rule.groups:
                # Evaluate domain
                domain = rule.domain_force
                if domain:
                    try:
                        # Simple evaluation
                        pass
                    except:
                        pass
                print(f"  User MATCHES this rule's groups: {bool(matching_groups or not rule.groups)}")
        
        # Check ACLs
        print("\n--- Checking ACLs for ir.attachment ---")
        acls = env['ir.model.access'].search([('model_id.model', '=', 'ir.attachment'), ('active', '=', True)])
        for acl in acls:
            if acl.group_id.id in user.groups_id.ids or not acl.group_id:
                print(f"ACL: {acl.name} | Group: {acl.group_id.full_name if acl.group_id else 'Global'} | Read: {acl.perm_read}")

if __name__ == "__main__":
    debug_access()
