#!/usr/bin/env python3
"""
DevNavigator Campaign Manager GUI
Complete tkinter UI for email campaigns, database management, and tracking
"""
import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from dotenv import load_dotenv
import threading

load_dotenv()

# Import our modules
from send_test_emails import EmailTemplateManager, EmailSender, EMAIL_ALIASES
from tracking import EmailTracker


class DevNavigatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DevNavigator Campaign Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        self.db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.template_manager = EmailTemplateManager(self.db_path)
        self.email_sender = EmailSender()
        self.tracker = EmailTracker()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_send_tab()
        self.create_database_tab()
        self.create_tracking_tab()
        self.create_templates_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
    
    def create_send_tab(self):
        """Send emails tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📧 Send Emails")
        
        # Title
        title = ttk.Label(frame, text="Send Email Campaign", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Template selection
        template_frame = ttk.LabelFrame(frame, text="Select Template", padding=10)
        template_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(template_frame, text="Template:").pack(side=tk.LEFT, padx=5)
        self.template_var = tk.StringVar()
        templates = self.get_templates()
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, 
                                      values=templates, state='readonly', width=30)
        template_combo.pack(side=tk.LEFT, padx=5)
        if templates:
            template_combo.current(0)
        
        # Recipient selection
        recipient_frame = ttk.LabelFrame(frame, text="Select Recipients", padding=10)
        recipient_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(recipient_frame, text="Send to:").pack(side=tk.LEFT, padx=5)
        self.recipient_var = tk.StringVar(value="all")
        ttk.Radiobutton(recipient_frame, text="All", variable=self.recipient_var, 
                       value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(recipient_frame, text="Specific emails", variable=self.recipient_var, 
                       value="specific").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(recipient_frame, text="By country", variable=self.recipient_var, 
                       value="country").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(recipient_frame, text="Exclude", variable=self.recipient_var, 
                       value="exclude").pack(side=tk.LEFT, padx=5)
        
        # Recipient details
        details_frame = ttk.LabelFrame(frame, text="Recipient Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(details_frame, text="Emails (comma-separated) or Country code:").pack(anchor=tk.W)
        self.recipient_input = tk.Text(details_frame, height=3, width=50)
        self.recipient_input.pack(fill=tk.X, pady=5)
        
        ttk.Label(details_frame, text="Limit (max recipients):").pack(anchor=tk.W)
        self.limit_var = tk.StringVar(value="100")
        ttk.Entry(details_frame, textvariable=self.limit_var, width=10).pack(anchor=tk.W)
        
        # Options
        options_frame = ttk.LabelFrame(frame, text="Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Dry run (preview only)", 
                       variable=self.dry_run_var).pack(anchor=tk.W)
        
        # Action buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Preview", command=self.preview_send).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Send Emails!", command=self.send_emails).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=lambda: self.recipient_input.delete('1.0', tk.END)).pack(side=tk.LEFT, padx=5)
    
    def create_database_tab(self):
        """Database viewer tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💾 Database")
        
        # Title
        title = ttk.Label(frame, text="Email Contacts Database", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Refresh", command=self.refresh_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export to CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_contact).pack(side=tk.LEFT, padx=5)
        
        # Table with scrollbars
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview
        columns = ('Email', 'Name', 'Company', 'Country', 'Sent', 'Opened')
        self.db_tree = ttk.Treeview(table_frame, columns=columns, height=20)
        self.db_tree.column('#0', width=0)
        self.db_tree.column('Email', anchor=tk.W, width=200)
        self.db_tree.column('Name', anchor=tk.W, width=120)
        self.db_tree.column('Company', anchor=tk.W, width=120)
        self.db_tree.column('Country', anchor=tk.CENTER, width=80)
        self.db_tree.column('Sent', anchor=tk.CENTER, width=60)
        self.db_tree.column('Opened', anchor=tk.CENTER, width=60)
        
        self.db_tree.heading('Email', text='Email')
        self.db_tree.heading('Name', text='Name')
        self.db_tree.heading('Company', text='Company')
        self.db_tree.heading('Country', text='Country')
        self.db_tree.heading('Sent', text='Sent')
        self.db_tree.heading('Opened', text='Opened')
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.db_tree.yview)
        self.db_tree.configure(yscroll=scrollbar.set)
        
        self.db_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_database()
    
    def create_tracking_tab(self):
        """Tracking statistics tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Tracking")
        
        # Title
        title = ttk.Label(frame, text="Campaign Tracking & Statistics", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Stats frame
        stats_frame = ttk.LabelFrame(frame, text="Overall Statistics", padding=15)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=80, state=tk.DISABLED)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Refresh Stats", command=self.refresh_tracking).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Start Tracking Server", command=self.start_tracking_server).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tracking()
    
    def create_templates_tab(self):
        """Templates management tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📝 Templates")
        
        # Title
        title = ttk.Label(frame, text="Email Templates", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Templates list
        list_frame = ttk.LabelFrame(frame, text="Available Templates", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.templates_list = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.templates_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.templates_list.yview)
        
        self.refresh_templates_list()
    
    def get_templates(self):
        """Get list of templates"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM email_templates ORDER BY name")
            templates = [row[0] for row in cursor.fetchall()]
            conn.close()
            return templates
        except:
            return []
    
    def refresh_database(self):
        """Refresh database view"""
        # Clear existing
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT email, name, company, country, sent, opened 
                FROM contacts ORDER BY email
            """)
            
            for row in cursor.fetchall():
                values = (row[0], row[1] or '', row[2] or '', row[3] or '', 
                         '✓' if row[4] else '✗', '✓' if row[5] else '✗')
                self.db_tree.insert('', tk.END, values=values)
            
            conn.close()
            self.status_var.set(f"Database: {len(self.db_tree.get_children())} contacts")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load database: {e}")
    
    def refresh_tracking(self):
        """Refresh tracking statistics"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        
        stats = self.tracker.get_tracking_stats()
        
        if stats:
            text = f"""
📊 EMAIL TRACKING STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📧 Total Sent:    {stats['total_sent']} emails
👁️  Opened:       {stats['opens']} ({stats['open_rate']})
🔗 Clicked:       {stats['clicks']} ({stats['click_rate']})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 DETAILED PER-EMAIL TRACKING:

"""
            detailed = self.tracker.get_detailed_tracking()
            if detailed:
                for email, total, opens, clicks, last_open, last_click in detailed:
                    text += f"\n📧 {email}\n"
                    text += f"   Opens:  {opens or 0}/{total}\n"
                    text += f"   Clicks: {clicks or 0}/{total}\n"
            else:
                text += "  No tracking data yet\n"
            
            self.stats_text.insert('1.0', text)
        else:
            text = "❌ No tracking data available\n\nTo enable tracking:\n1. Start tracking server: python3 tracking.py setup-server\n2. Send emails with tracking enabled"
            self.stats_text.insert('1.0', text)
        
        self.stats_text.config(state=tk.DISABLED)
    
    def refresh_templates_list(self):
        """Refresh templates list"""
        self.templates_list.delete(0, tk.END)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, subject, is_default FROM email_templates ORDER BY name")
            
            for name, subject, is_default in cursor.fetchall():
                marker = "⭐ " if is_default else "   "
                display = f"{marker}{name}: {subject[:40]}..."
                self.templates_list.insert(tk.END, display)
            
            conn.close()
        except:
            pass
    
    def preview_send(self):
        """Preview send without actually sending"""
        template = self.template_var.get()
        if not template:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        recipients = self.get_recipients()
        if not recipients:
            messagebox.showwarning("Warning", "No recipients selected")
            return
        
        preview_text = f"""
PREVIEW: Would send to {len(recipients)} recipient(s)

Template: {template}
Sender: {EMAIL_ALIASES.get(template, 'DevNavigator Team')}

Recipients:
"""
        for email in recipients[:10]:
            preview_text += f"  • {email}\n"
        
        if len(recipients) > 10:
            preview_text += f"  ... and {len(recipients) - 10} more\n"
        
        messagebox.showinfo("Send Preview", preview_text)
    
    def send_emails(self):
        """Send emails"""
        template = self.template_var.get()
        if not template:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        recipients = self.get_recipients()
        if not recipients:
            messagebox.showwarning("Warning", "No recipients selected")
            return
        
        # Confirm
        confirm = messagebox.askyesno("Confirm", 
            f"Send '{template}' to {len(recipients)} recipient(s)?\n\nThis will actually send emails!")
        
        if not confirm:
            return
        
        # Send in thread to prevent UI freeze
        def send_thread():
            try:
                self.status_var.set(f"Sending {len(recipients)} emails...")
                
                subject, body = self.template_manager.get_template(template)
                from_name = EMAIL_ALIASES.get(template, 'DevNavigator Team')
                
                sent = 0
                for email in recipients:
                    try:
                        success, _ = self.email_sender.send_test_email(
                            email, subject, body, from_name=from_name
                        )
                        if success:
                            sent += 1
                    except:
                        pass
                
                self.status_var.set(f"✓ Sent {sent}/{len(recipients)} emails")
                messagebox.showinfo("Success", f"Sent {sent}/{len(recipients)} emails successfully!")
                self.refresh_database()
                self.refresh_tracking()
            
            except Exception as e:
                self.status_var.set(f"✗ Error: {str(e)}")
                messagebox.showerror("Error", f"Send failed: {e}")
        
        thread = threading.Thread(target=send_thread)
        thread.start()
    
    def get_recipients(self):
        """Get recipient list based on selection"""
        mode = self.recipient_var.get()
        input_text = self.recipient_input.get('1.0', tk.END).strip()
        
        try:
            limit = int(self.limit_var.get())
        except:
            limit = 100
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if mode == "all":
                cursor.execute("SELECT email FROM contacts WHERE sent = 0 LIMIT ?", (limit,))
            elif mode == "specific":
                emails = [e.strip() for e in input_text.split(',')]
                placeholders = ','.join(['?' for _ in emails])
                cursor.execute(f"SELECT email FROM contacts WHERE email IN ({placeholders})", emails)
            elif mode == "country":
                country = input_text.upper()
                cursor.execute("SELECT email FROM contacts WHERE country = ? LIMIT ?", (country, limit))
            elif mode == "exclude":
                exclude_emails = [e.strip() for e in input_text.split(',')]
                placeholders = ','.join(['?' for _ in exclude_emails])
                cursor.execute(f"SELECT email FROM contacts WHERE email NOT IN ({placeholders}) AND sent = 0 LIMIT ?", 
                             exclude_emails + [limit])
            
            recipients = [row[0] for row in cursor.fetchall()]
            conn.close()
            return recipients
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not get recipients: {e}")
            return []
    
    def export_csv(self):
        """Export database to CSV"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT email, name, company, country, sent, opened FROM contacts")
            
            with open(file_path, 'w') as f:
                f.write("Email,Name,Company,Country,Sent,Opened\n")
                for row in cursor.fetchall():
                    f.write(f"{row[0]},{row[1] or ''},{row[2] or ''},{row[3] or ''},{row[4]},{row[5]}\n")
            
            conn.close()
            messagebox.showinfo("Success", f"Exported to {file_path}")
            self.status_var.set(f"Exported database to {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def delete_contact(self):
        """Delete selected contact"""
        selection = self.db_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a contact to delete")
            return
        
        item = selection[0]
        email = self.db_tree.item(item)['values'][0]
        
        confirm = messagebox.askyesno("Confirm", f"Delete {email}?")
        if not confirm:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            
            self.db_tree.delete(item)
            self.status_var.set(f"Deleted {email}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {e}")
    
    def start_tracking_server(self):
        """Start tracking server"""
        messagebox.showinfo("Tracking Server", 
            "To start the tracking server, run in terminal:\n\n" +
            "python3 tracking.py setup-server\n\n" +
            "This will start the HTTP server for tracking opens and clicks.")


def main():
    root = tk.Tk()
    app = DevNavigatorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
