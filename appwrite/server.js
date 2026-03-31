const express = require("express");
const cors = require("cors");
const sqlite3 = require("sqlite3").verbose();

const app = express();
app.use(cors());
app.use(express.json());

// Connect to your existing database
const db = new sqlite3.Database("./user.db", (err) => {
  if (err) console.error("DB error:", err);
  else console.log("Connected to user.db");
});

// Make sure users table exists (only runs once)
db.run(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT,
  email TEXT UNIQUE,
  password TEXT,
  role TEXT
)
`);

app.post("/api/register", (req, res) => {
  const { username, email, password, role } = req.body;

  if (!username || !email || !password) {
    return res.json({ success: false, error: "Missing fields" });
  }

  const sql = `INSERT INTO users (username, email, password, role)
               VALUES (?, ?, ?, ?)`;

  db.run(sql, [username, email, password, role], function (err) {
    if (err) {
      if (err.message.includes("UNIQUE")) {
        return res.json({ success: false, error: "Email already exists" });
      }
      return res.json({ success: false, error: err.message });
    }

    res.json({ success: true, userId: this.lastID });
  });
});

app.post("/api/login", (req, res) => {
  const { email, password } = req.body;

  const sql = `SELECT * FROM users WHERE email = ? AND password = ?`;

  db.get(sql, [email, password], (err, row) => {
    if (err) return res.json({ success: false, error: err.message });

    if (!row) {
      return res.json({ success: false, error: "Invalid email or password" });
    }

    res.json({ success: true, user: { username: row.username, email: row.email } });
  });
});

const HOST = process.env.HOST || "0.0.0.0";
const PORT = process.env.PORT || 3000;

app.listen(PORT, HOST, () =>
  console.log(`Server running on http://${HOST}:${PORT}`)
);
