import sys
sys.path.append('/Users/selamou/Desktop/odoo18-project/odoo')
import odoo
from odoo import api, SUPERUSER_ID

def fix_attachments():
    odoo.tools.config.parse_config(['-c', '/Users/selamou/Desktop/odoo18-project/odoo.conf'])
    db_name = 'odoo18'
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Find all attachments linked to execution.progress via the M2M relation
        cr.execute("SELECT progress_id, attachment_id FROM execution_progress_attachment_rel")
        links = cr.fetchall()
        
        for progress_id, attachment_id in links:
            attachment = env['ir.attachment'].browse(attachment_id)
            if attachment.exists() and not attachment.res_id:
                print(f"Linking Attachment {attachment_id} to Execution Progress {progress_id}")
                attachment.write({
                    'res_model': 'execution.progress',
                    'res_id': progress_id,
                })
        
        cr.commit()
        print("Done fixing attachments.")

if __name__ == "__main__":
    fix_attachments()
