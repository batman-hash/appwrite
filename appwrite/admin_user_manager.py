import tkinter as tk
import sqlite3
import bcrypt
from tkinter import messagebox
import os

# =========================
# DATABASE (SINGLE, SAFE CONNECTION)
# =========================

DB_PATH = os.path.join(os.path.dirname(__file__), "user.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Base table (works with old or new DB)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT
)
""")
conn.commit()

# Ensure new columns exist for password reset flow
cursor.execute("PRAGMA table_info(users)")
_columns = {row[1] for row in cursor.fetchall()}
if "reset_requested" not in _columns:
    cursor.execute("ALTER TABLE users ADD COLUMN reset_requested INTEGER DEFAULT 0")
    conn.commit()
if "reset_requested_at" not in _columns:
    cursor.execute("ALTER TABLE users ADD COLUMN reset_requested_at TEXT")
    conn.commit()

# Make sure old users have a role
cursor.execute("UPDATE users SET role='user' WHERE role IS NULL")
conn.commit()

# Ensure there is at least one admin
cursor.execute("SELECT * FROM users WHERE role='admin'")
if not cursor.fetchone():
    default_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        ("admin@local", default_hash, "admin")
    )
    conn.commit()

print(f"Connected to database: {DB_PATH}")

# =========================
# TKINTER WINDOW
# =========================

root = tk.Tk()
root.title("Secure Admin User Manager")
root.geometry("520x620")

# =========================
# FUNCTIONS
# =========================

AUTO_REFRESH_MS = 10_000
_auto_refresh_job = None

def refresh_users():
    user_listbox.delete(0, tk.END)
    cursor.execute("SELECT id, email, role, reset_requested FROM users")
    rows = cursor.fetchall()

    if not rows:
        user_listbox.insert(tk.END, "No users found in database")
        return

    for row in rows:
        reset_flag = "RESET" if row[3] else ""
        suffix = f" | {reset_flag}" if reset_flag else ""
        user_listbox.insert(tk.END, f"{row[0]} | {row[1]} | {row[2]}{suffix}")

def start_auto_refresh():
    global _auto_refresh_job
    if _auto_refresh_job is not None:
        root.after_cancel(_auto_refresh_job)

    def _tick():
        refresh_users()
        global _auto_refresh_job
        _auto_refresh_job = root.after(AUTO_REFRESH_MS, _tick)

    _auto_refresh_job = root.after(AUTO_REFRESH_MS, _tick)

def admin_login():
    email = admin_email.get().strip()
    password = admin_password.get().strip()

    if not email or not password:
        messagebox.showerror("Admin", "Enter email and password")
        return

    cursor.execute(
        "SELECT password FROM users WHERE email = ? AND role = 'admin'",
        (email,)
    )
    row = cursor.fetchone()

    if row and bcrypt.checkpw(password.encode(), row[0].encode()):
        messagebox.showinfo("Admin", "Access granted")
        frame_admin_panel.pack(fill="x", padx=10, pady=5)
        refresh_users()  # LOAD USERS ONLY AFTER LOGIN
        start_auto_refresh()
    else:
        messagebox.showerror("Admin", "Invalid admin credentials")

def add_user():
    email = new_email.get().strip()
    password = new_password.get().strip()

    if not email or not password:
        messagebox.showerror("Error", "Email and password required")
        return

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
            (email, hashed, "user")
        )
        conn.commit()

        messagebox.showinfo("Success", "User added and stored permanently")
        new_email.delete(0, tk.END)
        new_password.delete(0, tk.END)
        refresh_users()

    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists")

def delete_selected_user():
    selection = user_listbox.curselection()
    if not selection:
        messagebox.showwarning("Delete User", "Select a user first")
        return

    selected_text = user_listbox.get(selection[0])

    # Prevent deleting placeholder text
    if "Login as admin" in selected_text or "No users found" in selected_text:
        messagebox.showwarning("Delete User", "You must log in first")
        return

    user_id = selected_text.split(" | ")[0]

    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] == "admin":
        messagebox.showerror("Delete User", "You cannot delete the admin account")
        return

    confirm = messagebox.askyesno(
        "Delete User",
        f"Are you sure you want to delete user ID {user_id}?"
    )

    if confirm:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        refresh_users()
        messagebox.showinfo("Delete User", "User deleted permanently")

def reset_password_for_email():
    email = reset_email.get().strip()
    new_pw = reset_password.get().strip()

    if not email or not new_pw:
        messagebox.showerror("Reset Password", "Email and new password required")
        return

    cursor.execute("SELECT id, role FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Reset Password", "Email not found")
        return
    if row[1] == "admin":
        messagebox.showerror("Reset Password", "You cannot reset the admin account here")
        return

    hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "UPDATE users SET password = ?, reset_requested = 0, reset_requested_at = NULL WHERE email = ?",
        (hashed, email)
    )
    conn.commit()
    messagebox.showinfo("Reset Password", "Password updated")
    reset_email.delete(0, tk.END)
    reset_password.delete(0, tk.END)
    refresh_users()

def forgot_password():
    popup = tk.Toplevel(root)
    popup.title("Forgot Password")
    popup.geometry("350x180")

    tk.Label(popup, text="Enter your email").pack(pady=10)
    email_entry = tk.Entry(popup, width=40)
    email_entry.pack()

    def submit_request():
        email = email_entry.get().strip()

        if not email:
            messagebox.showerror("Error", "Enter your email")
            return

        cursor.execute("SELECT id, role FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()

        if not row:
            messagebox.showerror("Error", "Email not found")
            return
        if row[1] == "admin":
            messagebox.showerror("Error", "Admin accounts cannot request reset")
            return

        cursor.execute(
            "UPDATE users SET reset_requested = 1, reset_requested_at = datetime('now') WHERE email = ?",
            (email,)
        )
        conn.commit()

        messagebox.showinfo(
            "Request Sent",
            "Password reset requested. Admin will review it."
        )
        popup.destroy()

    tk.Button(popup, text="Send Reset Request", command=submit_request).pack(pady=20)

def view_db_users():
    popup = tk.Toplevel(root)
    popup.title("Database Users")
    popup.geometry("600x350")

    listbox = tk.Listbox(popup, width=90)
    listbox.pack(padx=10, pady=10, fill="both", expand=True)

    cursor.execute("SELECT id, email, role, reset_requested, reset_requested_at FROM users")
    rows = cursor.fetchall()

    if not rows:
        listbox.insert(tk.END, "No users found in database")
        return

    for row in rows:
        listbox.insert(
            tk.END,
            f"{row[0]} | {row[1]} | {row[2]} | reset={row[3]} | at={row[4]}"
        )

def send_reset_emails_to_pending():
    """Send reset emails to all users who have requested password reset."""
    cursor.execute(
        "SELECT id, email FROM users WHERE reset_requested = 1 AND role != 'admin'"
    )
    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo("Send Emails", "No pending password reset requests.")
        return

    sent_count = 0
    for user_id, email in rows:
        # In production, integrate with email service here
        # For now, show info and clear the flag
        messagebox.showinfo(
            "Send Reset Email",
            f"Would send reset email to:\n\nEmail: {email}\nUser ID: {user_id}"
        )
        sent_count += 1

    messagebox.showinfo(
        "Send Emails",
        f"Processed {sent_count} reset request(s).\n\nIn production, emails would be sent via SMTP."
    )

def send_reset_to_selected():
    """Send reset email to a selected user."""
    selection = user_listbox.curselection()
    if not selection:
        messagebox.showwarning("Send Email", "Select a user first")
        return

    selected_text = user_listbox.get(selection[0])

    if "Login as admin" in selected_text or "No users found" in selected_text:
        messagebox.showwarning("Send Email", "You must log in first")
        return

    user_id = selected_text.split(" | ")[0]

    cursor.execute("SELECT email, role, reset_requested FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        messagebox.showerror("Send Email", "User not found")
        return

    email, role, reset_requested = row

    if role == "admin":
        messagebox.showerror("Send Email", "Cannot send reset to admin account")
        return

    # Show email preview
    messagebox.showinfo(
        "Send Reset Email",
        f"Reset email would be sent to:\n\nEmail: {email}\nUser ID: {user_id}\n\nStatus: {'Pending request' if reset_requested == 1 else 'No request'}"
    )

    # If they had a request, mark it as notified (optional)
    if reset_requested == 1:
        cursor.execute(
            "UPDATE users SET reset_requested = 2 WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        refresh_users()

# =========================
# UI LAYOUT
# =========================

# --- ADMIN LOGIN (ONLY GATE) ---
frame_admin = tk.LabelFrame(root, text="Admin Login", padx=10, pady=10)
frame_admin.pack(fill="x", padx=10, pady=10)

tk.Label(frame_admin, text="Admin Email").pack()
admin_email = tk.Entry(frame_admin, width=50)
admin_email.insert(0, "admin@local")
admin_email.pack()

tk.Label(frame_admin, text="Admin Password").pack()
admin_password = tk.Entry(frame_admin, width=50, show="*")
admin_password.insert(0, "admin123")
admin_password.pack()

tk.Button(frame_admin, text="Login", command=admin_login).pack(pady=5)
tk.Button(frame_admin, text="Forgot Password", command=forgot_password).pack(pady=5)

# --- ADMIN PANEL (HIDDEN UNTIL LOGIN) ---
frame_admin_panel = tk.LabelFrame(root, text="Admin Control Panel", padx=10, pady=10)

tk.Label(frame_admin_panel, text="New User Email").pack()
new_email = tk.Entry(frame_admin_panel, width=50)
new_email.pack()

tk.Label(frame_admin_panel, text="New User Password").pack()
new_password = tk.Entry(frame_admin_panel, width=50, show="*")
new_password.pack()

tk.Button(frame_admin_panel, text="Add User", command=add_user).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="Delete Selected User",
    command=delete_selected_user
).pack(pady=5)

tk.Label(frame_admin_panel, text="Reset User Password (by email)").pack(pady=(10, 0))
reset_email = tk.Entry(frame_admin_panel, width=50)
reset_email.pack()
reset_password = tk.Entry(frame_admin_panel, width=50, show="*")
reset_password.pack()
tk.Button(
    frame_admin_panel,
    text="Reset Password",
    command=reset_password_for_email
).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="View DB Users",
    command=view_db_users
).pack(pady=5)

tk.Button(
    frame_admin_panel,
    text="Send Reset Email to Selected",
    command=send_reset_to_selected
).pack(pady=(10, 5))

tk.Button(
    frame_admin_panel,
    text="Send All Pending Reset Emails",
    command=send_reset_emails_to_pending
).pack(pady=5)

# --- USER LIST (HIDDEN DATA UNTIL LOGIN) ---
tk.Label(root, text="Stored Users (Admin View)").pack(pady=(10, 0))
user_listbox = tk.Listbox(root, width=70)
user_listbox.pack(pady=5)

# Placeholder before login
user_listbox.insert(tk.END, "Login as admin to view users")

# =========================
# CLEAN EXIT
# =========================

def on_close():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
