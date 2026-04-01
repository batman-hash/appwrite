import tkinter as tk
import sqlite3
import bcrypt
from tkinter import messagebox
import os
import uuid
from kernel.bridge.app_locks import acquire_process_locks

# =========================
# DATABASE PATH (DEFINE FIRST)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "user.db")
RESET_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8011")
PROJECT_LOCK_PATH = os.path.join(BASE_DIR, "project.pid")
ADMIN_LOCK_PATH = os.path.join(BASE_DIR, "admin_user_manager.pid")
PROJECT_SINGLE_INSTANCE_ENABLED = os.getenv("PROJECT_SINGLE_INSTANCE", "true").lower() == "true"
SINGLE_INSTANCE_ENABLED = os.getenv("SINGLE_INSTANCE", "true").lower() == "true"

print("Using database:", DB_PATH)


def acquire_single_instance_lock_or_exit():
    project_lock = PROJECT_LOCK_PATH if PROJECT_SINGLE_INSTANCE_ENABLED else None
    app_lock = ADMIN_LOCK_PATH if SINGLE_INSTANCE_ENABLED else None
    ok, msg = acquire_process_locks(
        project_lock_path=project_lock,
        app_lock_path=app_lock,
        project_label="Another project process",
        app_label="Another admin manager process",
    )
    if not ok:
        print(msg)
        raise SystemExit(1)


acquire_single_instance_lock_or_exit()

# =========================
# CONNECT
# =========================

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
cursor.execute("""
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Ensure new columns exist for password reset flow
cursor.execute("PRAGMA table_info(users)")
_columns = {row[1] for row in cursor.fetchall()}
if "username" not in _columns:
    cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
    conn.commit()
if "plain_password" not in _columns:
    cursor.execute("ALTER TABLE users ADD COLUMN plain_password TEXT")
    conn.commit()
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
root.geometry("580x760")

# =========================
# FUNCTIONS
# =========================

AUTO_REFRESH_MS = 10_000
_auto_refresh_job = None
_admin_logged_in = False


def get_selected_user_id():
    selection = user_listbox.curselection()
    if not selection:
        return None

    selected_text = user_listbox.get(selection[0])
    if "Login as admin" in selected_text or "No users found" in selected_text:
        return None

    user_id = selected_text.split(" | ")[0].strip()
    if not user_id.isdigit():
        return None
    return int(user_id)

def refresh_users():
    user_listbox.delete(0, tk.END)
    cursor.execute(
        "SELECT id, username, email, role, reset_requested, plain_password FROM users ORDER BY id"
    )
    rows = cursor.fetchall()

    if not rows:
        user_listbox.insert(tk.END, "No users found in database")
        return

    for row in rows:
        user_id, username, email, role, reset_requested, plain_password = row
        username = username or "(empty)"
        plain_password = plain_password or "(not stored)"
        reset_flag = "RESET" if reset_requested else ""
        suffix = f" | {reset_flag}" if reset_flag else ""
        user_listbox.insert(
            tk.END,
            f"{user_id} | {username} | {email} | {role} | PW:{plain_password}{suffix}"
        )

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
    global _admin_logged_in
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
        _admin_logged_in = True
        messagebox.showinfo("Admin", "Access granted")
        frame_admin_panel.pack(fill="x", padx=10, pady=5)
        refresh_users()  # LOAD USERS ONLY AFTER LOGIN
        start_auto_refresh()
    else:
        messagebox.showerror("Admin", "Invalid admin credentials")

def add_user():
    username = new_username.get().strip()
    email = new_email.get().strip()
    password = new_password.get().strip()
    role = new_role_var.get().strip() or "user"

    if not email or not password:
        messagebox.showerror("Error", "Email and password required")
        return

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, plain_password, role) VALUES (?, ?, ?, ?, ?)",
            (username, email, hashed, password, role)
        )
        conn.commit()

        messagebox.showinfo("Success", "User added and stored permanently")
        new_username.delete(0, tk.END)
        new_email.delete(0, tk.END)
        new_password.delete(0, tk.END)
        new_role_var.set("user")
        refresh_users()

    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Email already exists")


def load_selected_user_for_edit():
    user_id = get_selected_user_id()
    if user_id is None:
        messagebox.showwarning("Load User", "Select a valid user first")
        return

    cursor.execute(
        "SELECT username, email, role, plain_password FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Load User", "User not found")
        return

    username, email, role, plain_password = row
    new_username.delete(0, tk.END)
    new_email.delete(0, tk.END)
    new_password.delete(0, tk.END)
    new_username.insert(0, username or "")
    new_email.insert(0, email or "")
    new_password.insert(0, plain_password or "")
    new_role_var.set(role or "user")
    messagebox.showinfo("Load User", f"Loaded user ID {user_id} into form.")


def update_selected_user():
    user_id = get_selected_user_id()
    if user_id is None:
        messagebox.showwarning("Update User", "Select a valid user first")
        return

    username = new_username.get().strip()
    email = new_email.get().strip()
    password = new_password.get().strip()
    role = new_role_var.get().strip() or "user"

    if not email:
        messagebox.showerror("Update User", "Email is required")
        return

    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Update User", "User not found")
        return

    old_role = row[0] or "user"
    if old_role == "admin" and role != "admin":
        messagebox.showerror("Update User", "Cannot demote admin account")
        return

    try:
        if password:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "UPDATE users SET username = ?, email = ?, role = ?, password = ?, plain_password = ? WHERE id = ?",
                (username, email, role, hashed, password, user_id),
            )
        else:
            cursor.execute(
                "UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?",
                (username, email, role, user_id),
            )
        conn.commit()
        refresh_users()
        messagebox.showinfo("Update User", f"User ID {user_id} updated successfully")
    except sqlite3.IntegrityError:
        messagebox.showerror("Update User", "Email already exists")

def delete_selected_user():
    user_id = get_selected_user_id()
    if user_id is None:
        messagebox.showwarning("Delete User", "Select a user first")
        return

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
        "UPDATE users SET password = ?, plain_password = ?, reset_requested = 0, reset_requested_at = NULL WHERE email = ?",
        (hashed, new_pw, email)
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


def view_password_storage():
    popup = tk.Toplevel(root)
    popup.title("Stored Passwords (Hash)")
    popup.geometry("900x380")

    tk.Label(
        popup,
        text="Username | Email | Stored Password (bcrypt hash) | Plain Password",
        fg="#555"
    ).pack(pady=(8, 0))

    listbox = tk.Listbox(popup, width=140)
    listbox.pack(padx=10, pady=10, fill="both", expand=True)

    cursor.execute("SELECT id, username, email, password, plain_password FROM users ORDER BY id")
    rows = cursor.fetchall()

    if not rows:
        listbox.insert(tk.END, "No users found in database")
        return

    for row in rows:
        user_id, username, email, password_hash, plain_password = row
        username = username or "(empty)"
        plain_password = plain_password or "(not stored)"
        listbox.insert(
            tk.END,
            f"{user_id} | {username} | {email} | {password_hash} | {plain_password}"
        )

def create_reset_link_for_email(email):
    token = uuid.uuid4().hex
    cursor.execute(
        "INSERT INTO reset_tokens (email, token) VALUES (?, ?)",
        (email, token)
    )
    conn.commit()
    return f"{RESET_BASE_URL}/reset/{token}"

def show_selected_password():
    user_id = get_selected_user_id()
    if user_id is None:
        messagebox.showwarning("Show Password", "Select a user first")
        return
    cursor.execute(
        "SELECT username, email, password, plain_password FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Show Password", "User not found")
        return

    username, email, password_hash, plain_password = row
    username = username or "(empty)"
    plain_password = plain_password or "(not stored)"
    messagebox.showinfo(
        "Selected User Password",
        f"ID: {user_id}\nUsername: {username}\nEmail: {email}\n\nPlain: {plain_password}\n\nHash: {password_hash}"
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
        reset_link = create_reset_link_for_email(email)
        # In production, integrate with email service here
        # For now, show reset link so admin can send/copy it.
        messagebox.showinfo(
            "Send Reset Email",
            f"Would send reset email to:\n\nEmail: {email}\nUser ID: {user_id}\n\nReset link:\n{reset_link}"
        )
        sent_count += 1

    messagebox.showinfo(
        "Send Emails",
        f"Processed {sent_count} reset request(s).\n\nIn production, emails would be sent via SMTP."
    )

def send_reset_to_selected():
    """Send reset email to a selected user."""
    user_id = get_selected_user_id()
    if user_id is None:
        messagebox.showwarning("Send Email", "Select a user first")
        return

    cursor.execute("SELECT email, role, reset_requested FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        messagebox.showerror("Send Email", "User not found")
        return

    email, role, reset_requested = row

    if role == "admin":
        messagebox.showerror("Send Email", "Cannot send reset to admin account")
        return

    reset_link = create_reset_link_for_email(email)

    # Show email preview + real reset link
    messagebox.showinfo(
        "Send Reset Email",
        f"Reset email would be sent to:\n\nEmail: {email}\nUser ID: {user_id}\n\nStatus: {'Pending request' if reset_requested == 1 else 'No request'}\n\nReset link:\n{reset_link}"
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

tk.Label(frame_admin_panel, text="New Username").pack()
new_username = tk.Entry(frame_admin_panel, width=50)
new_username.pack()

tk.Label(frame_admin_panel, text="New User Email").pack()
new_email = tk.Entry(frame_admin_panel, width=50)
new_email.pack()

tk.Label(frame_admin_panel, text="New User Password").pack()
new_password = tk.Entry(frame_admin_panel, width=50, show="*")
new_password.pack()

tk.Label(frame_admin_panel, text="Role").pack()
new_role_var = tk.StringVar(value="user")
tk.OptionMenu(frame_admin_panel, new_role_var, "user", "admin").pack()

tk.Button(frame_admin_panel, text="Add User", command=add_user).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="Load Selected Into Form",
    command=load_selected_user_for_edit
).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="Update Selected User",
    command=update_selected_user
).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="Delete Selected User",
    command=delete_selected_user
).pack(pady=5)
tk.Button(
    frame_admin_panel,
    text="Show Selected Password",
    command=show_selected_password
).pack(pady=5)

tk.Label(frame_admin_panel, text="Reset User Password (by email)").pack(pady=(10, 0))
reset_email = tk.Entry(frame_admin_panel, width=50)
reset_email.pack()
reset_password = tk.Entry(frame_admin_panel, width=50, show="*")
reset_password.pack()

show_passwords_var = tk.BooleanVar(value=False)

def toggle_password_visibility():
    show_char = "" if show_passwords_var.get() else "*"
    admin_password.config(show=show_char)
    new_password.config(show=show_char)
    reset_password.config(show=show_char)

tk.Checkbutton(
    frame_admin_panel,
    text="Show Password Fields",
    variable=show_passwords_var,
    command=toggle_password_visibility
).pack(pady=(4, 6))

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
    text="View Stored Passwords",
    command=view_password_storage
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
