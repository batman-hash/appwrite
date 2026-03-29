#!/usr/bin/env python3
"""
DevNavigator Campaign Manager GUI
Complete tkinter UI for email campaigns, database management, and tracking
"""
import csv
import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import threading

load_dotenv()

# Import our modules
from python_engine.database_manager import DatabaseManager
from send_test_emails import (
    EmailTemplateManager,
    EmailSender,
    EMAIL_ALIASES,
    get_campaign_register_link,
    get_campaign_visuals,
    render_email_content,
)
from tracking import EmailTracker


class DevNavigatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DevNavigator Campaign Manager")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        self.db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_manager = DatabaseManager(self.db_path)
        self.template_manager = EmailTemplateManager(self.db_path)
        self.email_sender = EmailSender()
        self.tracker = EmailTracker()

        # Status bar state is used during initial tab setup.
        self.status_var = tk.StringVar(value="Ready")
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_send_tab()
        self.create_database_tab()
        self.create_tracking_tab()
        self.create_templates_tab()
        
        # Status bar
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
        default_template = self.template_manager.get_default_template_name()
        if default_template:
            self.template_var.set(default_template)
        elif templates:
            template_combo.current(0)
        
        # Quick send buttons
        quick_frame = ttk.LabelFrame(frame, text="Quick Send Options", padding=10)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(quick_frame, text="📬 Send Approved Recent", 
                  command=self.send_to_extracted).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(quick_frame, text="📊 Show Recent Imports", 
                  command=self.show_extracted_emails).pack(side=tk.LEFT, padx=5, pady=5)
        self.extracted_count_var = tk.StringVar(value="")
        ttk.Label(quick_frame, textvariable=self.extracted_count_var, 
                 foreground="green", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        self.update_extracted_count()
        
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
        ttk.Button(button_frame, text="Archive Selected", command=self.archive_selected_contacts).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Archive Sent", command=self.archive_sent_contacts).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Unarchive Selected", command=self.unarchive_selected_contacts).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import Leads CSV", command=self.import_campaign_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📬 Recent Imports", 
                  command=self.show_extracted_emails).pack(side=tk.LEFT, padx=5)
        
        self.db_filter_options = {
            'All contacts': 'all',
            'Ready to send': 'ready',
            'Needs review': 'review',
            'Recent imports': 'recent',
            'Sent': 'sent',
            'Archived': 'archived',
        }
        ttk.Label(button_frame, text="View:").pack(side=tk.LEFT, padx=(15, 5))
        self.db_filter_var = tk.StringVar(value='All contacts')
        filter_combo = ttk.Combobox(
            button_frame,
            textvariable=self.db_filter_var,
            values=list(self.db_filter_options.keys()),
            state='readonly',
            width=16,
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda _event: self.refresh_database())
        
        # Info label
        self.db_info_var = tk.StringVar()
        ttk.Label(button_frame, textvariable=self.db_info_var, foreground="green").pack(side=tk.LEFT, padx=20)
        
        # Table with scrollbars
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview
        columns = ('Email', 'Name', 'Company', 'Source', 'Consent', 'Status', 'Sent', 'Extracted')
        self.db_tree = ttk.Treeview(table_frame, columns=columns, height=20)
        self.db_tree.column('#0', width=0)
        self.db_tree.column('Email', anchor=tk.W, width=180)
        self.db_tree.column('Name', anchor=tk.W, width=100)
        self.db_tree.column('Company', anchor=tk.W, width=100)
        self.db_tree.column('Source', anchor=tk.W, width=120)
        self.db_tree.column('Consent', anchor=tk.CENTER, width=60)
        self.db_tree.column('Status', anchor=tk.W, width=110)
        self.db_tree.column('Sent', anchor=tk.CENTER, width=50)
        self.db_tree.column('Extracted', anchor=tk.W, width=140)
        
        self.db_tree.heading('Email', text='Email')
        self.db_tree.heading('Name', text='Name')
        self.db_tree.heading('Company', text='Company')
        self.db_tree.heading('Source', text='Source')
        self.db_tree.heading('Consent', text='Consent')
        self.db_tree.heading('Status', text='Status')
        self.db_tree.heading('Sent', text='Sent')
        self.db_tree.heading('Extracted', text='Extracted')
        
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
            cursor.execute("""
                SELECT name
                FROM email_templates
                ORDER BY is_default DESC, name ASC
            """)
            templates = [row[0] for row in cursor.fetchall()]
            conn.close()
            return templates
        except:
            return []

    def get_selected_template(self):
        """Return the selected template or fall back to the DB default."""
        selected = self.template_var.get().strip()
        if selected:
            return selected
        return self.template_manager.get_default_template_name()

    def show_preview_window(self, title, content):
        """Display long preview text in a scrollable dialog."""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("760x640")

        frame = ttk.Frame(window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        text = tk.Text(frame, wrap=tk.WORD)
        text.insert('1.0', content)
        text.config(state=tk.DISABLED)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)

        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def get_current_queue_filter(self):
        """Get the currently selected database filter."""
        return self.db_filter_options.get(self.db_filter_var.get(), 'all')
    
    def refresh_database(self):
        """Refresh database view"""
        # Clear existing
        for item in self.db_tree.get_children():
            self.db_tree.delete(item)
        
        try:
            contacts = self.db_manager.get_contacts(queue=self.get_current_queue_filter())
            summary = self.db_manager.get_queue_summary()

            for contact in contacts:
                values = (
                    contact['email'],
                    contact['name'] or '',
                    contact['company'] or '',
                    contact['source'] or '',
                    '✓' if contact['consent'] else '✗',
                    contact['queue_status'],
                    '✓' if contact['sent'] else '✗',
                    contact['created_at'] or 'N/A',
                )
                self.db_tree.insert('', tk.END, values=values)
            
            shown = len(contacts)
            total = summary['total_contacts']
            self.status_var.set(f"Database: showing {shown} of {total} contacts")
            self.db_info_var.set(
                f"Ready: {summary['ready_to_send']} | Review: {summary['needs_review']} | Recent: {summary['recent_imports']} | Archived: {summary['archived_count']}"
            )
            self.update_extracted_count()
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
            cursor.execute("""
                SELECT name, subject, is_default
                FROM email_templates
                ORDER BY is_default DESC, name ASC
            """)
            
            for name, subject, is_default in cursor.fetchall():
                marker = "⭐ " if is_default else "   "
                display = f"{marker}{name}: {subject[:40]}..."
                self.templates_list.insert(tk.END, display)
            
            conn.close()
        except:
            pass
    
    def preview_send(self):
        """Preview send without actually sending"""
        template = self.get_selected_template()
        if not template:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        recipients = self.get_recipients()
        if not recipients:
            messagebox.showwarning("Warning", "No recipients selected")
            return
        
        subject, body = self.template_manager.get_template(template)
        sample_email = recipients[0]
        rendered_subject, rendered_body = render_email_content(
            to_email=sample_email,
            subject=subject,
            body=body,
            template_name=template,
            add_tracking=False,
        )
        visuals = get_campaign_visuals(template)

        preview_text = f"""PREVIEW: Would send to {len(recipients)} recipient(s)

Template: {template}
Sender: {EMAIL_ALIASES.get(template, 'DevNavigator Team')}
Register link: {get_campaign_register_link(template) or 'not set'}
Visuals attached: {len(visuals)}
Sample recipient: {sample_email}

Subject:
{rendered_subject}

Body:
{rendered_body}

Visual files:
"""
        for image_path in visuals:
            preview_text += f"{image_path}\n"

        preview_text += """

Recipients:
"""
        for email in recipients[:10]:
            preview_text += f"  • {email}\n"
        
        if len(recipients) > 10:
            preview_text += f"  ... and {len(recipients) - 10} more\n"
        
        self.show_preview_window("Send Preview", preview_text)
    
    def send_emails(self):
        """Send emails"""
        template = self.get_selected_template()
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
                            email, subject, body, template_name=template, from_name=from_name
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
        sendable_where = self.db_manager.SENDABLE_WHERE
        
        try:
            limit = int(self.limit_var.get())
        except:
            limit = 100

        if mode == "specific":
            emails = [e.strip() for e in input_text.split(',') if e.strip()]
            if not emails:
                return []
        else:
            emails = []

        if mode == "exclude":
            exclude_emails = [e.strip() for e in input_text.split(',') if e.strip()]
        else:
            exclude_emails = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if mode == "all":
                cursor.execute(f"SELECT email FROM contacts WHERE {sendable_where} LIMIT ?", (limit,))
            elif mode == "specific":
                placeholders = ','.join(['?' for _ in emails])
                cursor.execute(
                    f"SELECT email FROM contacts WHERE email IN ({placeholders}) AND {sendable_where}",
                    emails,
                )
            elif mode == "country":
                country = input_text.upper()
                cursor.execute(
                    f"SELECT email FROM contacts WHERE country = ? AND {sendable_where} LIMIT ?",
                    (country, limit),
                )
            elif mode == "exclude":
                if exclude_emails:
                    placeholders = ','.join(['?' for _ in exclude_emails])
                    cursor.execute(
                        f"SELECT email FROM contacts WHERE email NOT IN ({placeholders}) AND {sendable_where} LIMIT ?",
                        exclude_emails + [limit],
                    )
                else:
                    cursor.execute(f"SELECT email FROM contacts WHERE {sendable_where} LIMIT ?", (limit,))
            
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
            
            contacts = self.db_manager.get_contacts(queue=self.get_current_queue_filter(), limit=None)

            with open(file_path, 'w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['Email', 'Name', 'Company', 'Country', 'Source', 'Consent', 'Status', 'Sent', 'Extracted'])
                for contact in contacts:
                    writer.writerow([
                        contact['email'],
                        contact['name'] or '',
                        contact['company'] or '',
                        contact['country'] or '',
                        contact['source'] or '',
                        contact['consent'],
                        contact['queue_status'],
                        contact['sent'],
                        contact['created_at'] or '',
                    ])

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

    def archive_selected_contacts(self):
        """Archive selected contacts from the active queue."""
        selection = self.db_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more contacts to archive")
            return

        emails = [self.db_tree.item(item)['values'][0] for item in selection]
        confirm = messagebox.askyesno(
            "Confirm Archive",
            f"Archive {len(emails)} selected contact(s)?\n\nThey will disappear from active views but stay in the database."
        )
        if not confirm:
            return

        archived = self.db_manager.archive_contacts(emails=emails)
        self.refresh_database()
        self.status_var.set(f"Archived {archived} selected contacts")

    def archive_sent_contacts(self):
        """Archive all currently sent contacts."""
        confirm = messagebox.askyesno(
            "Confirm Archive",
            "Archive all sent contacts?\n\nThey will disappear from active views but stay in the database."
        )
        if not confirm:
            return

        archived = self.db_manager.archive_contacts(sent_only=True)
        self.refresh_database()
        self.status_var.set(f"Archived {archived} sent contacts")

    def unarchive_selected_contacts(self):
        """Restore selected archived contacts."""
        selection = self.db_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select one or more contacts to restore")
            return

        emails = [self.db_tree.item(item)['values'][0] for item in selection]
        restored = self.db_manager.unarchive_contacts(emails=emails)
        self.refresh_database()
        self.status_var.set(f"Restored {restored} archived contacts")
    
    def start_tracking_server(self):
        """Start tracking server"""
        messagebox.showinfo("Tracking Server", 
            "To start the tracking server, run in terminal:\n\n" +
            "python3 tracking.py setup-server\n\n" +
            "This will start the HTTP server for tracking opens and clicks.")

    def import_campaign_csv(self):
        """Import a local leads file into the database."""
        default_dir = Path.cwd() / 'Work_From_Home_Campaign' / 'Contacts_Leads'
        file_path = filedialog.askopenfilename(
            initialdir=str(default_dir if default_dir.exists() else Path.cwd()),
            initialfile='emails_list.csv',
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        )

        if not file_path:
            return

        source = 'work_from_home_campaign' if 'Work_From_Home_Campaign' in Path(file_path).parts else 'csv_upload'
        imported, duplicates, errors = self.db_manager.import_contacts_file(file_path, source=source)

        lines = [
            f"Imported: {imported}",
            f"Duplicates: {duplicates}",
            "Queue status: imported contacts require review before sending",
        ]
        if errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(errors[:10])
            if len(errors) > 10:
                lines.append(f"... and {len(errors) - 10} more")

        self.refresh_database()
        messagebox.showinfo("Import Complete", "\n".join(lines))
        self.status_var.set(f"Imported {imported} contacts from {Path(file_path).name}")
    
    def get_extracted_emails(self, hours=24):
        """Get recently extracted emails (unsent)"""
        try:
            return self.db_manager.get_contacts(queue='recent', recent_hours=hours)
        except:
            return []
    
    def count_extracted_emails(self):
        """Count recently extracted unsent emails"""
        return len(self.get_extracted_emails())
    
    def update_extracted_count(self):
        """Update the extracted emails counter"""
        summary = self.db_manager.get_queue_summary()
        if summary['recent_imports'] > 0:
            self.extracted_count_var.set(
                f"📥 {summary['recent_imports']} recent imports | {summary['ready_to_send']} ready to send"
            )
        else:
            self.extracted_count_var.set("No recent imports")
    
    def show_extracted_emails(self):
        """Show list of recently extracted emails"""
        extracted = self.get_extracted_emails()
        
        if not extracted:
            messagebox.showinfo("Recent Imports", "No recent imports found")
            return
        
        info = f"📥 RECENT IMPORTS ({len(extracted)} total)\n"
        info += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for contact in extracted[:20]:
            info += f"📧 {contact['email']}\n"
            if contact['name']:
                info += f"   Name: {contact['name']}\n"
            if contact['company']:
                info += f"   Company: {contact['company']}\n"
            if contact['country']:
                info += f"   Country: {contact['country']}\n"
            info += f"   Source: {contact['source'] or 'manual'}\n"
            info += f"   Status: {contact['queue_status']}\n"
            info += "\n"
        
        if len(extracted) > 20:
            info += f"\n... and {len(extracted) - 20} more emails"
        
        messagebox.showinfo("Recent Imports", info)
    
    def send_to_extracted(self):
        """Send to recently imported contacts that are approved for sending."""
        template = self.get_selected_template()
        if not template:
            messagebox.showwarning("Warning", "Please select a template")
            return
        
        extracted = self.db_manager.get_contacts(queue='recent_ready', recent_hours=24)
        if not extracted:
            messagebox.showwarning(
                "Warning",
                "No recently imported contacts are approved and ready to send.\n\nReview the Database tab first."
            )
            return
        
        recipients = [contact['email'] for contact in extracted]
        
        # Preview
        preview_text = f"""
📬 SEND TO {len(recipients)} APPROVED RECENT CONTACTS

Template: {template}
Sender: {EMAIL_ALIASES.get(template, 'DevNavigator Team')}

Recipients:
"""
        for email in recipients[:15]:
            info = next(contact for contact in extracted if contact['email'] == email)
            preview_text += f"  • {email}"
            if info['name']:
                preview_text += f" ({info['name']})"
            preview_text += "\n"
        
        if len(recipients) > 15:
            preview_text += f"  ... and {len(recipients) - 15} more\n"
        
        # Confirm
        confirm = messagebox.askyesno("Confirm Send", preview_text + "\nSend now?")
        
        if not confirm:
            return
        
        # Send in thread
        def send_thread():
            try:
                self.status_var.set(f"Sending to {len(recipients)} approved recent contacts...")
                
                subject, body = self.template_manager.get_template(template)
                from_name = EMAIL_ALIASES.get(template, 'DevNavigator Team')
                
                sent = 0
                for email in recipients:
                    try:
                        success, _ = self.email_sender.send_test_email(
                            email, subject, body, template_name=template, from_name=from_name
                        )
                        if success:
                            sent += 1
                    except:
                        pass
                
                self.status_var.set(f"✓ Sent {sent}/{len(recipients)} approved recent contacts")
                messagebox.showinfo("Success", 
                    f"✓ Sent {sent}/{len(recipients)} emails to approved recent contacts!")
                self.refresh_database()
                self.refresh_tracking()
                self.update_extracted_count()
            
            except Exception as e:
                self.status_var.set(f"✗ Error: {str(e)}")
                messagebox.showerror("Error", f"Send failed: {e}")
        
        thread = threading.Thread(target=send_thread)
        thread.start()


def main():
    root = tk.Tk()
    app = DevNavigatorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
