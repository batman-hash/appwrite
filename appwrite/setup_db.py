import sqlite3
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "user.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT
)
""")
conn.commit()

# Add admin user if not exists
email = "admin@local"
password = "admin123"

cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
if cursor.fetchone():
    print(f"User {email} already exists in database")
else:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email, hashed, "admin")
    )
    conn.commit()
    print(f"Admin user {email} added to database")

# Show all users
cursor.execute("SELECT id, email, role FROM users")
rows = cursor.fetchall()
print("\nUsers in database:")
for row in rows:
    print(f"  ID: {row[0]} | Email: {row[1]} | Role: {row[2]}")

conn.close()
