"""
Email Template Manager
Handles email templates - default and custom
"""
import sqlite3
import os
from typing import List, Dict, Optional
import json
from string import Template


class TemplateManager:
    """Manages email templates"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
    
    def add_template(self, name: str, subject: str, body: str, is_default: bool = False) -> bool:
        """
        Add a new email template
        Variables in template can be: {name}, {email}, {date}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO email_templates (name, subject, body, is_default)
                VALUES (?, ?, ?, ?)
            """, (name, subject, body, 1 if is_default else 0))
            
            conn.commit()
            print(f"✓ Template '{name}' added successfully")
            return True
        except sqlite3.IntegrityError:
            print(f"✗ Template '{name}' already exists")
            return False
        finally:
            conn.close()
    
    def get_template(self, template_id: int = None, name: str = None) -> Optional[Dict]:
        """Get template by ID or name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if template_id:
                cursor.execute("""
                    SELECT id, name, subject, body, is_default
                    FROM email_templates WHERE id = ?
                """, (template_id,))
            elif name:
                cursor.execute("""
                    SELECT id, name, subject, body, is_default
                    FROM email_templates WHERE name = ?
                """, (name,))
            else:
                cursor.execute("""
                    SELECT id, name, subject, body, is_default
                    FROM email_templates WHERE is_default = 1
                """)
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'subject': result[2],
                    'body': result[3],
                    'is_default': result[4]
                }
            return None
        finally:
            conn.close()
    
    def get_all_templates(self) -> List[Dict]:
        """Get all templates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, subject, is_default
                FROM email_templates ORDER BY is_default DESC
            """)
            
            templates = []
            for row in cursor.fetchall():
                templates.append({
                    'id': row[0],
                    'name': row[1],
                    'subject': row[2],
                    'is_default': row[3]
                })
            return templates
        finally:
            conn.close()
    
    def render_template(self, template_id: int = None, name: str = None, context: Dict = None) -> Dict:
        """
        Render template with context variables
        context: dict with keys like 'name', 'email', etc.
        """
        if context is None:
            context = {}
        
        template = self.get_template(template_id, name)
        
        if not template:
            raise ValueError("Template not found")
        
        # Create template objects with safe substitution
        subject_tmpl = Template(template['subject'])
        body_tmpl = Template(template['body'])
        
        # Render with provided context
        rendered_subject = subject_tmpl.safe_substitute(context)
        rendered_body = body_tmpl.safe_substitute(context)
        
        return {
            'template_id': template['id'],
            'template_name': template['name'],
            'subject': rendered_subject,
            'body': rendered_body
        }
    
    def update_template(self, template_id: int, subject: str = None, body: str = None) -> bool:
        """Update template content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if subject and body:
                cursor.execute("""
                    UPDATE email_templates
                    SET subject = ?, body = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (subject, body, template_id))
            elif subject:
                cursor.execute("""
                    UPDATE email_templates
                    SET subject = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (subject, template_id))
            elif body:
                cursor.execute("""
                    UPDATE email_templates
                    SET body = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (body, template_id))
            
            conn.commit()
            print(f"✓ Template {template_id} updated")
            return True
        except Exception as e:
            print(f"✗ Error updating template: {e}")
            return False
        finally:
            conn.close()
    
    def delete_template(self, template_id: int) -> bool:
        """Delete template (except default)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if default
            cursor.execute("SELECT is_default FROM email_templates WHERE id = ?", (template_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print("✗ Cannot delete default template")
                return False
            
            cursor.execute("DELETE FROM email_templates WHERE id = ?", (template_id,))
            conn.commit()
            print(f"✓ Template {template_id} deleted")
            return True
        except Exception as e:
            print(f"✗ Error deleting template: {e}")
            return False
        finally:
            conn.close()


def create_sample_templates(db_path: str = None):
    """Create sample templates for testing"""
    manager = TemplateManager(db_path)
    
    # Template 1: Educational App
    manager.add_template(
        name='educational_app',
        subject='Join us in launching an innovative learning platform 🎓',
        body="""Hi $name,

We're excited to share our new educational app designed specifically for children!

Our platform offers:
- Interactive learning experiences
- Safe, secure browsing for kids
- Engaging content across multiple subjects
- Parental controls and monitoring

We believe education should be fun, engaging, and accessible to all children.

Would you like to learn more about our platform? Simply reply to this email!

Best regards,
DevNavigator Team
matteopennacchia43@gmail.com"""
    )
    
    # Template 2: Partnership Opportunity
    manager.add_template(
        name='partnership_opportunity',
        subject='Partnership Opportunity: New Children\'s Learning App',
        body="""Hi $name,

We're reaching out to explore potential partnership opportunities with you for our new children's learning platform.

Our Mission: Making education engaging, interactive, and accessible

Your expertise could be valuable in:
- Content creation
- Educational methodology
- Parent engagement
- Technical integration

Let's discuss how we can collaborate!

Interested in learning more? Contact us today!

Best regards,
DevNavigator Team
matteopennacchia43@gmail.com"""
    )
    
    # Template 3: Quick Inquiry
    manager.add_template(
        name='quick_inquiry',
        subject='Quick Question about Your Expertise',
        body="""Hi $name,

A quick question: Would you be interested in discussing a new educational initiative?

We're building something special and think your insights could be valuable.

Let me know if you'd be open to a brief conversation!

Best regards,
DevNavigator
matteopennacchia43@gmail.com"""
    )
    
    print("\n✓ Sample templates created successfully")


if __name__ == "__main__":
    db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
    create_sample_templates(db_path)
    
    manager = TemplateManager(db_path)
    print("\nAvailable templates:")
    for template in manager.get_all_templates():
        marker = "[DEFAULT]" if template['is_default'] else "         "
        print(f"  {marker} {template['name']}: {template['subject']}")
