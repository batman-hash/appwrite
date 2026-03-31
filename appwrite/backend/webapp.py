from flask import Flask, request, redirect, session, jsonify, send_from_directory
import sqlite3
import os
import time
import json
import base64
import secrets
import hashlib
import hmac
import pdb
import argparse
import sys
import ssl
from flask import g, request
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
try:
    from flask_cors import CORS
except ImportError:
    def CORS(*args, **kwargs):
        return None
import bcrypt
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl
from urllib import request as urllib_request
from urllib import error as urllib_error
import smtplib
import uuid
import base64
import ipaddress
from html import escape as html_escape
from email.message import EmailMessage
from decimal import Decimal, InvalidOperation
from wsgiref.simple_server import make_server, WSGIRequestHandler
from werkzeug.exceptions import HTTPException

# =========================
# APP SETUP
# =========================

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
PROJECT_CONFIG_PATH = os.path.join(CONFIG_DIR, "project_config.json")
PROJECT_CONFIG = {}
if os.path.exists(PROJECT_CONFIG_PATH):
    try:
        with open(PROJECT_CONFIG_PATH, "r", encoding="utf-8") as _config_file:
            PROJECT_CONFIG = json.load(_config_file) or {}
    except Exception:
        PROJECT_CONFIG = {}
def _resolve_frontend_dir():
    configured = ((PROJECT_CONFIG.get("paths") or {}).get("frontend_dir") or "").strip()
    candidates = [configured] if configured else []
    candidates.extend(["frontend", "frontend1"])

    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = candidate if os.path.isabs(candidate) else os.path.join(PROJECT_ROOT, candidate)
        if os.path.isdir(candidate_path):
            return candidate_path

    return os.path.join(PROJECT_ROOT, "frontend")


FRONTEND_DIR = _resolve_frontend_dir()
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    app.secret_key = "dev-only-change-me"
    print("WARNING: SECRET_KEY/FLASK_SECRET_KEY not set. Using insecure development fallback.")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
DB = os.path.join(os.getenv("DATA_DIR", PROJECT_ROOT), "user.db")
REQUEST_OBS_PATH = os.path.join(CONFIG_DIR, "request_observations.json")
REQUEST_OBS_MAX_ITEMS = int(os.getenv("REQUEST_OBS_MAX_ITEMS", "500"))
REQUEST_PAYLOAD_MAX = int(os.getenv("REQUEST_PAYLOAD_MAX", "1024"))
SHARED_FILE_MAX_BYTES = int(os.getenv("SHARED_FILE_MAX_BYTES", "2500000"))
REQUEST_OBS_ENABLED = os.getenv("REQUEST_OBS_ENABLED", "true").lower() == "true"
LOCAL_DEVICE_ONLY = os.getenv("LOCAL_DEVICE_ONLY", "true").lower() == "true"
ALLOWED_DEVICE_IP = os.getenv("ALLOWED_DEVICE_IP", "").strip()
DEFAULT_APP_PORT = int(((PROJECT_CONFIG.get("ports") or {}).get("app") or 8011))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", f"http://localhost:{DEFAULT_APP_PORT}")
STATIC_BASE_URL = os.getenv("STATIC_BASE_URL", f"http://localhost:{DEFAULT_APP_PORT}")
DEFAULT_ORIGINS = f"http://localhost:{DEFAULT_APP_PORT},http://127.0.0.1:{DEFAULT_APP_PORT}"
allowed_origins = list(
    dict.fromkeys(
        o.strip().rstrip("/")
        for o in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")
        if o.strip()
    )
)
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"
APP_ENV = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development").strip().lower()
ENABLE_DEBUG_TOOLBAR = os.getenv("ENABLE_DEBUG_TOOLBAR", "false").lower() == "true"
ENABLE_PDB_ROUTE = os.getenv("ENABLE_PDB_ROUTE", "false").lower() == "true"
CHAT_ACTIVE_TTL_SECONDS = int(os.getenv("CHAT_ACTIVE_TTL_SECONDS", "300"))
ACTIVE_CHAT_USERS = {}
CHECKOUT_CODE_TTL_SECONDS = int(os.getenv("CHECKOUT_CODE_TTL_SECONDS", "600"))
CHECKOUT_VERIFIED_TTL_SECONDS = int(os.getenv("CHECKOUT_VERIFIED_TTL_SECONDS", "1800"))
CHECKOUT_VERIFICATIONS = {}
EMAIL_PROVIDER = (os.getenv("EMAIL_PROVIDER") or "auto").strip().lower()
NEWSLETTER_DEV_OPEN = os.getenv("NEWSLETTER_DEV_OPEN", "false").lower() == "true"
PORT_8081_ALLOWED_WINDOWS_USER = os.getenv(
    "PORT_8081_ALLOWED_WINDOWS_USER",
    r"DESKTOP-SFT4T0S\Utente",
)
TOKEN_PEPPER = os.getenv("TOKEN_PEPPER") or app.secret_key
PAYMENTS_ENABLED = os.getenv("PAYMENTS_ENABLED", "false").lower() == "true"
PAYPAL_CLIENT_ID = (os.getenv("PAYPAL_CLIENT_ID") or "").strip()
PAYPAL_CLIENT_SECRET = (os.getenv("PAYPAL_CLIENT_SECRET") or "").strip()
PAYPAL_ENV = (os.getenv("PAYPAL_ENV") or "sandbox").strip().lower()
PAYPAL_WEBHOOK_ID = (os.getenv("PAYPAL_WEBHOOK_ID") or "").strip()
STRIPE_SECRET_KEY = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
STRIPE_WEBHOOK_SECRET = (os.getenv("STRIPE_WEBHOOK_SECRET") or "").strip()
BTCPAY_BASE_URL = (os.getenv("BTCPAY_BASE_URL") or "").strip()
BTCPAY_API_KEY = (os.getenv("BTCPAY_API_KEY") or "").strip()
BTCPAY_STORE_ID = (os.getenv("BTCPAY_STORE_ID") or "").strip()
BTCPAY_WEBHOOK_SECRET = (os.getenv("BTCPAY_WEBHOOK_SECRET") or "").strip()
HTTPS_ENABLED = os.getenv("HTTPS_ENABLED", "false").lower() == "true"
SSL_CERT_FILE = (os.getenv("SSL_CERT_FILE") or "").strip()
SSL_KEY_FILE = (os.getenv("SSL_KEY_FILE") or "").strip()

app.config["DEBUG"] = DEBUG_MODE
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
app.config["SECRET_KEY"] = app.secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER") or os.getenv("SMTP_HOST", "")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
app.config["MAIL_USE_SSL"] = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USER")
app.config["MAIL_PASSWORD"] = (
    os.getenv("MAIL_PASSWORD")
    or os.getenv("SMTP_APP_PASSWORD")
    or os.getenv("SMTP_PASS")
)
app.config["MAIL_DEFAULT_SENDER"] = (
    os.getenv("MAIL_DEFAULT_SENDER")
    or os.getenv("SMTP_FROM")
    or os.getenv("MAIL_USERNAME")
    or os.getenv("SMTP_USER")
    or "no-reply@localhost"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = HTTPS_ENABLED
app.config["PREFERRED_URL_SCHEME"] = "https" if HTTPS_ENABLED else "http"

db_orm = SQLAlchemy(app)
mail = Mail(app)

CORS(
    app,
    resources={
        r"/api/*": {"origins": allowed_origins},
        r"/subscribe": {"origins": allowed_origins},
    },
)

if ENABLE_DEBUG_TOOLBAR:
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        DebugToolbarExtension(app)
        print("Flask-DebugToolbar enabled")
    except Exception as e:
        print("Failed to enable Flask-DebugToolbar:", e)


def acquire_single_instance_lock():
    # Lock paths disabled: always allow startup.
    return True


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _current_windows_user():
    domain = os.environ.get("USERDOMAIN", "").strip()
    user = os.environ.get("USERNAME", "").strip()
    if domain and user:
        return f"{domain}\\{user}"
    return user or ""


def _cleanup_checkout_verifications():
    now_ts = int(time.time())
    stale_keys = [
        key for key, item in CHECKOUT_VERIFICATIONS.items()
        if int(item.get("expires_at") or 0) <= now_ts
    ]
    for key in stale_keys:
        CHECKOUT_VERIFICATIONS.pop(key, None)


def _checkout_verification_key(order_code, client_ip):
    return f"{(order_code or '').strip()}::{(client_ip or '').strip()}"


def _is_valid_email(value):
    value = (value or "").strip()
    return bool(value and "@" in value and "." in value.split("@")[-1])


def _is_allowed_client(ip):
    if not LOCAL_DEVICE_ONLY:
        return True
    allowed = {"127.0.0.1", "::1"}
    allowed_device_ip = (ALLOWED_DEVICE_IP or "").strip().lower()
    if allowed_device_ip == "auto":
        try:
            parsed_ip = ipaddress.ip_address((ip or "").strip())
            # Allow Docker bridge / local private addresses when the app runs in a container.
            if parsed_ip.is_loopback or parsed_ip.is_private:
                return True
        except ValueError:
            pass
    elif ALLOWED_DEVICE_IP:
        allowed.add(ALLOWED_DEVICE_IP)
    return ip in allowed


def _request_bytes():
    headers_bytes = sum(len(k) + len(v) for k, v in request.headers.items())
    body_size = request.content_length or 0
    if body_size == 0:
        try:
            body_size = len(request.get_data(cache=True) or b"")
        except Exception:
            body_size = 0
    line_size = len(request.method) + len(request.full_path or request.path)
    return int(headers_bytes + body_size + line_size)


def _mark_chat_active(email):
    if email:
        ACTIVE_CHAT_USERS[email] = int(time.time())


def _chat_online_count():
    now_ts = int(time.time())
    stale = [
        email for email, ts in ACTIVE_CHAT_USERS.items()
        if (now_ts - int(ts)) > CHAT_ACTIVE_TTL_SECONDS
    ]
    for email in stale:
        ACTIVE_CHAT_USERS.pop(email, None)
    return len(ACTIVE_CHAT_USERS)


def _relation_bytes():
    q = request.query_string.decode("utf-8", errors="ignore")
    user_agent = request.headers.get("User-Agent", "")
    ref = request.headers.get("Referer", "")
    origin = request.headers.get("Origin", "")
    return int(len(request.path) + len(q) + len(user_agent) + len(ref) + len(origin))


def _payload_snippet():
    parts = [request.method, request.path]
    q = request.query_string.decode("utf-8", errors="ignore")
    if q:
        parts.append(q)
    try:
        raw_body = request.get_data(cache=True, as_text=True) or ""
    except Exception:
        raw_body = ""
    if raw_body:
        parts.append(raw_body[:REQUEST_PAYLOAD_MAX])
    merged = " | ".join(p.replace("\n", " ").replace("\r", " ") for p in parts)
    return merged[:REQUEST_PAYLOAD_MAX]


def _should_observe_request():
    if request.path.startswith("/__debugger__"):
        return False
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        return True
    if request.path.startswith("/api/"):
        return True
    return False


def append_request_observation():
    if not REQUEST_OBS_ENABLED or not _should_observe_request():
        return

    observation = {
        "ip": _client_ip(),
        "request_bytes": _request_bytes(),
        "relation_bytes": _relation_bytes(),
        "payload": _payload_snippet(),
        "method": request.method,
        "path": request.path,
        "created_at": int(time.time()),
    }

    try:
        existing = []
        if os.path.exists(REQUEST_OBS_PATH):
            with open(REQUEST_OBS_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    existing = loaded
        existing.append(observation)
        if len(existing) > REQUEST_OBS_MAX_ITEMS:
            existing = existing[-REQUEST_OBS_MAX_ITEMS:]
        tmp_path = REQUEST_OBS_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        os.replace(tmp_path, REQUEST_OBS_PATH)
    except Exception as e:
        print("request observation write failed:", e)

# runs BEFORE every request
@app.before_request
def start_timer():
    client_ip = _client_ip()
    if not _is_allowed_client(client_ip):
        return jsonify(success=False, error="Forbidden"), 403
    g.start_time = time.time()

# runs AFTER every request
@app.after_request
def log_time(response):
    if hasattr(g, "start_time"):
        duration = (time.time() - g.start_time) * 1000
        print(f"{request.method} {request.path} -> {duration:.2f} ms")
        response.headers["X-Response-Time-ms"] = f"{duration:.2f}"
    # Required for SharedArrayBuffer-based FFmpeg worker/core usage in modern Chrome.
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    append_request_observation()
    return response


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    if request.path.startswith("/api/"):
        return jsonify(success=False, error=error.description or error.name), error.code
    return error


@app.errorhandler(Exception)
def handle_unexpected_exception(error):
    if request.path.startswith("/api/"):
        print("API exception:", repr(error))
        return jsonify(success=False, error=str(error) or "Internal server error"), 500
    raise error

# =========================
# SERVE WEBSITE FILES
# =========================

@app.route("/")
def site():
    target = "root.html" if os.path.exists(os.path.join(FRONTEND_DIR, "root.html")) else "index.html"
    return send_from_directory(FRONTEND_DIR, target)

@app.route("/webapp.py")
@app.route("/webapp.py/")
@app.route("/backend/webapp.py")
def webapp_alias():
    # Browser request alias: open app root instead of exposing python source path.
    return redirect("/")

@app.route("/<path:filename>")
def files(filename):
    if filename in ("webapp.py", "backend/webapp.py"):
        return redirect("/")
    return send_from_directory(FRONTEND_DIR, filename)

# =========================
# DATABASE CONNECTION
# =========================

def conn():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c


class UserEmailMessageModel(db_orm.Model):
    __tablename__ = "user_email_messages"

    id = db_orm.Column(db_orm.Integer, primary_key=True)
    user_email = db_orm.Column(db_orm.Text, nullable=False)
    to_email = db_orm.Column(db_orm.Text, nullable=False)
    subject = db_orm.Column(db_orm.Text, nullable=False)
    body = db_orm.Column(db_orm.Text, nullable=False)
    status = db_orm.Column(db_orm.Text, nullable=False, default="pending")
    error = db_orm.Column(db_orm.Text)
    created_at = db_orm.Column(db_orm.DateTime)
    sent_at = db_orm.Column(db_orm.DateTime)

# =========================
# CREATE TABLES
# =========================

def init_db():
    with conn() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS activation_tokens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS email_tokens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            purpose TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS reset_tokens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS reset_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT,
            status TEXT NOT NULL DEFAULT 'requested',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            emailed_at TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS contact_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            username TEXT,
            email TEXT,
            recipient_email TEXT,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'new',
            emailed_user INTEGER NOT NULL DEFAULT 0,
            emailed_admin INTEGER NOT NULL DEFAULT 0,
            email_status TEXT NOT NULL DEFAULT 'pending',
            email_error TEXT,
            emailed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS subscribers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE NOT NULL,
            weighter TEXT,
            unsubscribed INTEGER NOT NULL DEFAULT 0,
            unsubscribe_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS campaigns(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS campaign_sends(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            subscriber_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(campaign_id, subscriber_id)
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS shared_files(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            image_data TEXT NOT NULL,
            uploader_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS user_email_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            to_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            currency TEXT NOT NULL DEFAULT 'USD',
            amount_total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'draft',
            source TEXT NOT NULL DEFAULT 'web',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS order_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id TEXT,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 1,
            line_total REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            provider TEXT NOT NULL,
            provider_payment_id TEXT,
            provider_checkout_url TEXT,
            amount REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL DEFAULT 'pending',
            destination_ref TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS payout_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination_label TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD',
            provider TEXT NOT NULL DEFAULT 'manual_bank',
            status TEXT NOT NULL DEFAULT 'requested',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        payout_columns = {row["name"] for row in db.execute("PRAGMA table_info(payout_requests)").fetchall()}
        if "provider_payout_id" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN provider_payout_id TEXT")
        if "provider_response_json" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN provider_response_json TEXT")
        if "failure_reason" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN failure_reason TEXT")
        if "executed_at" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN executed_at TIMESTAMP")
        if "account_holder" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN account_holder TEXT")
        if "bank_name" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN bank_name TEXT")
        if "account_number" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN account_number TEXT")
        if "iban" not in payout_columns:
            db.execute("ALTER TABLE payout_requests ADD COLUMN iban TEXT")
        db.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            event_type TEXT,
            event_id TEXT,
            signature TEXT,
            payload_json TEXT,
            processed INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_email TEXT,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        db.commit()


FAILED_LOGIN_LIMIT = int(os.getenv("FAILED_LOGIN_LIMIT", "3"))
FAILED_LOGIN_LOCK_HOURS = int(os.getenv("FAILED_LOGIN_LOCK_HOURS", "24"))


def _lock_until_timestamp():
    return int(time.time()) + (FAILED_LOGIN_LOCK_HOURS * 3600)


def _lock_message():
    return f"Too many failed attempts. This email is locked for {FAILED_LOGIN_LOCK_HOURS} hours."


def _is_user_locked(user_row):
    return int(user_row["locked_until"] or 0) > int(time.time())


def _reset_failed_login_state(email):
    with conn() as db:
        db.execute(
            """
            UPDATE users
            SET failed_login_count=0,
                locked_until=NULL
            WHERE email=?
            """,
            (email,),
        )
        db.commit()


def _register_failed_login_attempt(user_row):
    if not user_row:
        return {"locked": False, "attempts": 0}

    email = (user_row["email"] or "").strip().lower()
    attempts = int(user_row["failed_login_count"] or 0) + 1
    locked_until = None
    locked = False

    if attempts >= FAILED_LOGIN_LIMIT:
        attempts = FAILED_LOGIN_LIMIT
        locked_until = _lock_until_timestamp()
        locked = True

    with conn() as db:
        db.execute(
            """
            UPDATE users
            SET failed_login_count=?,
                locked_until=?
            WHERE email=?
            """,
            (attempts, locked_until, email),
        )
        db.commit()

    return {"locked": locked, "attempts": attempts, "locked_until": locked_until}


def _as_money(value):
    try:
        return float(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


def _safe_order_code():
    return f"CG-{int(time.time())}-{uuid.uuid4().hex[:8].upper()}"


def _append_audit_log(actor_email, action, details=""):
    try:
        with conn() as db:
            db.execute(
                "INSERT INTO audit_log(actor_email, action, details) VALUES (?, ?, ?)",
                (actor_email, action, details),
            )
            db.commit()
    except Exception:
        pass


def _payment_provider_ready(provider):
    provider = (provider or "").strip().lower()
    if provider == "paypal":
        return bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)
    if provider == "card":
        return bool(STRIPE_SECRET_KEY)
    if provider == "bitcoin":
        return bool(BTCPAY_BASE_URL and BTCPAY_API_KEY and BTCPAY_STORE_ID)
    return False


def _provider_checkout_url(provider, order_code):
    provider = (provider or "").strip().lower()
    if provider == "paypal":
        return f"{STATIC_BASE_URL}/paypal.html?order={order_code}"
    if provider == "card":
        return f"{STATIC_BASE_URL}/debit_card.html?order={order_code}"
    if provider == "bitcoin":
        return f"{STATIC_BASE_URL}/bitcoin.html?order={order_code}"
    return f"{STATIC_BASE_URL}/shop_cart.html"


def _stripe_checkout_success_url(order_code):
    return f"{STATIC_BASE_URL}/debit_card.html?stripe=success&order={order_code}"


def _stripe_checkout_cancel_url(order_code):
    return f"{STATIC_BASE_URL}/debit_card.html?stripe=cancel&order={order_code}"


def _paypal_api_base():
    if PAYPAL_ENV == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _paypal_basic_auth_headers(content_type="application/json"):
    token = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": content_type,
        "Accept": "application/json",
    }


def _paypal_api_request(path, method="GET", payload=None, headers=None, timeout=20):
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    data = None
    if payload is not None:
        if isinstance(payload, (bytes, bytearray)):
            data = payload
        else:
            data = json.dumps(payload).encode("utf-8")
            req_headers.setdefault("Content-Type", "application/json")
    req = urllib_request.Request(
        f"{_paypal_api_base()}{path}",
        data=data,
        headers=req_headers,
        method=method,
    )
    with urllib_request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def _paypal_access_token():
    payload = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    response = _paypal_api_request(
        "/v1/oauth2/token",
        method="POST",
        payload=payload,
        headers=_paypal_basic_auth_headers("application/x-www-form-urlencoded"),
    )
    return str(response.get("access_token") or "").strip()


def _btcpay_api_base():
    return BTCPAY_BASE_URL.rstrip("/")


def _btcpay_headers():
    return {
        "Authorization": f"token {BTCPAY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _btcpay_api_request(path, method="GET", payload=None, timeout=20):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        f"{_btcpay_api_base()}{path}",
        data=data,
        headers=_btcpay_headers(),
        method=method,
    )
    with urllib_request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def _create_btcpay_invoice(order, items):
    currency = (order.get("currency") or "USD").upper()
    checkout_url = f"{STATIC_BASE_URL}/bitcoin.html?order={order['order_code']}"
    payload = {
        "amount": _as_money(order.get("amount_total") or 0),
        "currency": currency,
        "orderId": order["order_code"],
        "metadata": {
            "orderCode": order["order_code"],
            "source": order.get("source") or "web",
            "itemCount": sum(max(1, int(item.get("quantity") or 1)) for item in items),
        },
        "checkout": {
            "redirectURL": f"{checkout_url}&btcpay=paid",
            "redirectAutomatically": True,
            "expirationMinutes": 30,
        },
    }
    if order.get("customer_email"):
        payload["buyerEmail"] = order["customer_email"]
    return _btcpay_api_request(
        f"/api/v1/stores/{BTCPAY_STORE_ID}/invoices",
        method="POST",
        payload=payload,
    )


def _get_btcpay_invoice(invoice_id):
    return _btcpay_api_request(
        f"/api/v1/stores/{BTCPAY_STORE_ID}/invoices/{invoice_id}",
        method="GET",
    )


def _verify_btcpay_signature(raw_payload, signature_header, secret):
    if not raw_payload or not signature_header or not secret:
        return False
    signature = signature_header.strip()
    if signature.lower().startswith("sha256="):
        signature = signature.split("=", 1)[1]
    computed = hmac.new(
        secret.encode("utf-8"),
        raw_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


def _find_order_by_btcpay_invoice_id(invoice_id):
    invoice_id = (invoice_id or "").strip()
    if not invoice_id:
        return None, None
    with conn() as db:
        payment_row = db.execute(
            """
            SELECT p.*, o.order_code
            FROM payments p
            JOIN orders o ON o.id = p.order_id
            WHERE p.provider='bitcoin' AND p.provider_payment_id=?
            ORDER BY p.id DESC
            LIMIT 1
            """,
            (invoice_id,),
        ).fetchone()
    if not payment_row:
        return None, None
    payload = _read_order_by_code(str(payment_row["order_code"] or "").strip())
    return payload, payment_row


def _finalize_btcpay_payment(order_code, invoice_id, metadata=None):
    payload = _read_order_by_code((order_code or "").strip())
    if not payload:
        return False, "Order not found", None

    with conn() as db:
        payment_row = db.execute(
            """
            SELECT *
            FROM payments
            WHERE order_id=? AND provider='bitcoin' AND provider_payment_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (payload["order"]["id"], (invoice_id or "").strip()),
        ).fetchone()
    if not payment_row:
        return False, "Payment session not found", payload

    if str(payment_row["status"] or "").strip().lower() == "paid":
        return True, None, payload

    _mark_order_payment_paid(
        payload["order"]["id"],
        "bitcoin",
        invoice_id,
        metadata=metadata,
    )
    return True, None, payload


def _paypal_bearer_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }


def _create_paypal_checkout_order(order, items):
    access_token = _paypal_access_token()
    currency = (order.get("currency") or "USD").upper()
    paypal_items = []
    item_total = Decimal("0.00")
    for item in items:
        quantity = max(1, int(item.get("quantity") or 1))
        unit_amount = Decimal(str(_as_money(item.get("unit_price") or 0))).quantize(Decimal("0.01"))
        line_total = (unit_amount * quantity).quantize(Decimal("0.01"))
        item_total += line_total
        paypal_items.append(
            {
                "name": str(item.get("product_name") or "Item")[:127],
                "quantity": str(quantity),
                "unit_amount": {
                    "currency_code": currency,
                    "value": f"{unit_amount:.2f}",
                },
                "category": "DIGITAL_GOODS",
                "sku": str(item.get("product_id") or "")[:127],
            }
        )
    total_value = Decimal(str(_as_money(order.get("amount_total") or 0))).quantize(Decimal("0.01"))
    if item_total != total_value:
        item_total = total_value
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": order["order_code"],
                "description": f"CYBERGHOST order {order['order_code']}",
                "amount": {
                    "currency_code": currency,
                    "value": f"{total_value:.2f}",
                    "breakdown": {
                        "item_total": {
                            "currency_code": currency,
                            "value": f"{item_total:.2f}",
                        }
                    },
                },
                "items": paypal_items,
                "custom_id": order["order_code"],
            }
        ],
        "application_context": {
            "brand_name": "CYBERGHOST",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "shipping_preference": "NO_SHIPPING",
            "return_url": f"{STATIC_BASE_URL}/paypal.html?paypal=success&order={order['order_code']}",
            "cancel_url": f"{STATIC_BASE_URL}/paypal.html?paypal=cancel&order={order['order_code']}",
        },
    }
    return _paypal_api_request(
        "/v2/checkout/orders",
        method="POST",
        payload=payload,
        headers=_paypal_bearer_headers(access_token),
    )


def _capture_paypal_order(paypal_order_id):
    access_token = _paypal_access_token()
    return _paypal_api_request(
        f"/v2/checkout/orders/{paypal_order_id}/capture",
        method="POST",
        payload={},
        headers=_paypal_bearer_headers(access_token),
    )


def _verify_paypal_webhook_signature(raw_payload, headers_map, webhook_event):
    if not PAYPAL_WEBHOOK_ID:
        raise RuntimeError("PAYPAL_WEBHOOK_ID is not configured")
    access_token = _paypal_access_token()
    payload = {
        "transmission_id": (headers_map.get("Paypal-Transmission-Id") or "").strip(),
        "transmission_time": (headers_map.get("Paypal-Transmission-Time") or "").strip(),
        "cert_url": (headers_map.get("Paypal-Cert-Url") or "").strip(),
        "auth_algo": (headers_map.get("Paypal-Auth-Algo") or "").strip(),
        "transmission_sig": (headers_map.get("Paypal-Transmission-Sig") or "").strip(),
        "webhook_id": PAYPAL_WEBHOOK_ID,
        "webhook_event": webhook_event,
    }
    if not all(payload[k] for k in ("transmission_id", "transmission_time", "cert_url", "auth_algo", "transmission_sig")):
        return {"verification_status": "FAILURE", "error": "Missing PayPal webhook verification headers"}
    return _paypal_api_request(
        "/v1/notifications/verify-webhook-signature",
        method="POST",
        payload=payload,
        headers=_paypal_bearer_headers(access_token),
    )


def _find_order_by_paypal_order_id(paypal_order_id):
    paypal_order_id = (paypal_order_id or "").strip()
    if not paypal_order_id:
        return None, None
    with conn() as db:
        payment_row = db.execute(
            """
            SELECT p.*, o.order_code
            FROM payments p
            JOIN orders o ON o.id = p.order_id
            WHERE p.provider='paypal' AND p.provider_payment_id=?
            ORDER BY p.id DESC
            LIMIT 1
            """,
            (paypal_order_id,),
        ).fetchone()
    if not payment_row:
        return None, None
    payload = _read_order_by_code(str(payment_row["order_code"] or "").strip())
    return payload, payment_row


def _finalize_paypal_payment(order_code, paypal_order_id, metadata=None):
    payload = _read_order_by_code((order_code or "").strip())
    if not payload:
        return False, "Order not found", None

    with conn() as db:
        payment_row = db.execute(
            """
            SELECT *
            FROM payments
            WHERE order_id=? AND provider='paypal' AND provider_payment_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (payload["order"]["id"], (paypal_order_id or "").strip()),
        ).fetchone()
    if not payment_row:
        return False, "Payment session not found", payload

    if str(payment_row["status"] or "").strip().lower() == "paid":
        return True, None, payload

    _mark_order_payment_paid(
        payload["order"]["id"],
        "paypal",
        paypal_order_id,
        metadata=metadata,
    )
    return True, None, payload


def _stripe_headers():
    token = base64.b64encode(f"{STRIPE_SECRET_KEY}:".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _ssl_context_from_env():
    if not HTTPS_ENABLED:
        return None
    if not SSL_CERT_FILE or not SSL_KEY_FILE:
        raise RuntimeError("HTTPS is enabled but SSL_CERT_FILE or SSL_KEY_FILE is missing.")
    cert_path = os.path.abspath(os.path.join(PROJECT_ROOT, SSL_CERT_FILE)) if not os.path.isabs(SSL_CERT_FILE) else SSL_CERT_FILE
    key_path = os.path.abspath(os.path.join(PROJECT_ROOT, SSL_KEY_FILE)) if not os.path.isabs(SSL_KEY_FILE) else SSL_KEY_FILE
    if not os.path.exists(cert_path):
        raise RuntimeError(f"SSL cert file not found: {cert_path}")
    if not os.path.exists(key_path):
        raise RuntimeError(f"SSL key file not found: {key_path}")
    return (cert_path, key_path)


class QuietWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        print("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def run_local_server(host, port):
    ssl_context = _ssl_context_from_env()
    with make_server(host, port, app, handler_class=QuietWSGIRequestHandler) as httpd:
        protocol = "http"
        if ssl_context:
            cert_path, key_path = ssl_context
            server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
            httpd.socket = server_ctx.wrap_socket(httpd.socket, server_side=True)
            protocol = "https"
            print("HTTPS enabled for local server.")
        print(f" * Running on {protocol}://{host}:{port}")
        httpd.serve_forever()


def _create_stripe_checkout_session(order, items):
    form = {
        "mode": "payment",
        "success_url": _stripe_checkout_success_url(order["order_code"]),
        "cancel_url": _stripe_checkout_cancel_url(order["order_code"]),
        "client_reference_id": order["order_code"],
        "metadata[order_code]": order["order_code"],
    }
    if order.get("customer_email"):
        form["customer_email"] = order["customer_email"]

    for idx, item in enumerate(items):
        unit_amount_cents = max(1, int(round(float(item["unit_price"] or 0) * 100)))
        form[f"line_items[{idx}][quantity]"] = int(item["quantity"] or 1)
        form[f"line_items[{idx}][price_data][currency]"] = (order.get("currency") or "USD").lower()
        form[f"line_items[{idx}][price_data][unit_amount]"] = unit_amount_cents
        form[f"line_items[{idx}][price_data][product_data][name]"] = item["product_name"]
        if item.get("product_id"):
            form[f"line_items[{idx}][price_data][product_data][metadata][product_id]"] = item["product_id"]

    encoded = urlencode(form, doseq=True).encode("utf-8")
    req = urllib_request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=encoded,
        headers=_stripe_headers(),
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload


def _verify_stripe_signature(raw_payload, signature_header, secret):
    if not raw_payload or not signature_header or not secret:
        return False
    parts = {}
    for chunk in signature_header.split(","):
        if "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        parts[k.strip()] = v.strip()
    timestamp = parts.get("t")
    expected = parts.get("v1")
    if not timestamp or not expected:
        return False
    signed = f"{timestamp}.{raw_payload}".encode("utf-8")
    computed = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected)


def _read_order_with_items(order_id):
    with conn() as db:
        order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            return None
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id=? ORDER BY id ASC",
            (order_id,),
        ).fetchall()
    return {
        "order": dict(order),
        "items": [dict(i) for i in items],
    }


def _read_order_by_code(order_code):
    with conn() as db:
        order = db.execute("SELECT * FROM orders WHERE order_code=?", (order_code,)).fetchone()
    if not order:
        return None
    return _read_order_with_items(order["id"])


def _recent_orders(limit=25):
    with conn() as db:
        orders = db.execute(
            """
            SELECT *
            FROM orders
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit or 25), 100)),),
        ).fetchall()
    return [dict(order) for order in orders]


def _customer_purchase_history(limit=25):
    with conn() as db:
        rows = db.execute(
            """
            SELECT
                COALESCE(NULLIF(o.customer_email, ''), NULLIF(o.customer_name, ''), 'guest') AS customer_key,
                MAX(o.customer_name) AS customer_name,
                MAX(o.customer_email) AS customer_email,
                COUNT(DISTINCT o.id) AS orders_count,
                SUM(oi.line_total) AS total_spent,
                MAX(o.created_at) AS last_order_at
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            GROUP BY COALESCE(NULLIF(o.customer_email, ''), NULLIF(o.customer_name, ''), 'guest')
            ORDER BY MAX(o.id) DESC
            LIMIT ?
            """,
            (max(1, min(int(limit or 25), 100)),),
        ).fetchall()

        items = []
        for row in rows:
            customer_key = row["customer_key"]
            bought_rows = db.execute(
                """
                SELECT
                    oi.product_name,
                    SUM(oi.quantity) AS quantity,
                    SUM(oi.line_total) AS total_amount
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                WHERE COALESCE(NULLIF(o.customer_email, ''), NULLIF(o.customer_name, ''), 'guest')=?
                GROUP BY oi.product_name
                ORDER BY SUM(oi.quantity) DESC, oi.product_name ASC
                """,
                (customer_key,),
            ).fetchall()
            items.append({
                "customer_key": customer_key,
                "customer_name": row["customer_name"] or "",
                "customer_email": row["customer_email"] or "",
                "orders_count": row["orders_count"] or 0,
                "total_spent": row["total_spent"] or 0,
                "last_order_at": row["last_order_at"],
                "items": [dict(item) for item in bought_rows],
            })
    return items


def _recent_payout_requests(limit=25):
    with conn() as db:
        rows = db.execute(
            """
            SELECT *
            FROM payout_requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit or 25), 100)),),
        ).fetchall()
    return [dict(row) for row in rows]


def _stripe_payouts_ready():
    return bool(STRIPE_SECRET_KEY and PAYMENTS_ENABLED)


def _create_stripe_payout(payout_row):
    amount_cents = max(1, int(round(float(payout_row["amount"] or 0) * 100)))
    form = {
        "amount": amount_cents,
        "currency": str(payout_row.get("currency") or "USD").lower(),
        "metadata[payout_request_id]": str(payout_row["id"]),
        "metadata[destination_label]": str(payout_row.get("destination_label") or ""),
        "metadata[account_holder]": str(payout_row.get("account_holder") or ""),
        "metadata[bank_name]": str(payout_row.get("bank_name") or ""),
        "metadata[account_number]": str(payout_row.get("account_number") or ""),
        "metadata[iban]": str(payout_row.get("iban") or ""),
    }
    encoded = urlencode(form, doseq=True).encode("utf-8")
    req = urllib_request.Request(
        "https://api.stripe.com/v1/payouts",
        data=encoded,
        headers=_stripe_headers(),
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload


def _mark_order_payment_paid(order_id, provider, provider_payment_id, metadata=None):
    with conn() as db:
        payment_row = db.execute(
            """
            SELECT id, metadata_json
            FROM payments
            WHERE order_id=? AND provider=? AND provider_payment_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (order_id, provider, provider_payment_id),
        ).fetchone()
        existing_meta = {}
        if payment_row and payment_row["metadata_json"]:
            try:
                existing_meta = json.loads(payment_row["metadata_json"])
            except Exception:
                existing_meta = {}
        merged_meta = {**existing_meta, **(metadata or {})}
        db.execute(
            """
            UPDATE payments
            SET status='paid', metadata_json=?, updated_at=CURRENT_TIMESTAMP
            WHERE order_id=? AND provider=? AND provider_payment_id=?
            """,
            (json.dumps(merged_meta), order_id, provider, provider_payment_id),
        )
        db.execute(
            "UPDATE orders SET status='paid', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (order_id,),
        )
        db.commit()


def _record_payment_submission(order_code, provider, provider_payment_id, details=None):
    payload = _read_order_by_code((order_code or "").strip())
    if not payload:
        return False, "Order not found", None

    provider = (provider or "").strip().lower()
    if provider not in ("paypal", "card", "bitcoin"):
        return False, "Unsupported provider", None

    details = details or {}
    normalized_payment_id = (provider_payment_id or "").strip()
    payment_row = None

    with conn() as db:
        if normalized_payment_id:
            payment_row = db.execute(
                """
                SELECT *
                FROM payments
                WHERE order_id=? AND provider=? AND provider_payment_id=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (payload["order"]["id"], provider, normalized_payment_id),
            ).fetchone()

        if not payment_row:
            payment_row = db.execute(
                """
                SELECT *
                FROM payments
                WHERE order_id=? AND provider=?
                ORDER BY id DESC
                LIMIT 1
                """,
                (payload["order"]["id"], provider),
            ).fetchone()

        if not payment_row:
            return False, "Payment record not found", None

        existing_meta = {}
        if payment_row["metadata_json"]:
            try:
                existing_meta = json.loads(payment_row["metadata_json"])
            except Exception:
                existing_meta = {}

        merged_meta = {**existing_meta, **details}
        destination_ref = (
            (details.get("reference") or "").strip()
            or (details.get("wallet") or "").strip()
            or (details.get("email") or "").strip()
            or (details.get("last4") or "").strip()
            or (payment_row["destination_ref"] or "").strip()
        )
        next_status = str(payment_row["status"] or "").strip().lower()
        if next_status not in ("paid", "submitted"):
            next_status = "submitted"

        db.execute(
            """
            UPDATE payments
            SET destination_ref=?,
                metadata_json=?,
                status=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                destination_ref or None,
                json.dumps(merged_meta),
                next_status,
                payment_row["id"],
            ),
        )
        if str(payload["order"]["status"] or "").strip().lower() != "paid":
            db.execute(
                "UPDATE orders SET status='payment_submitted', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (payload["order"]["id"],),
            )
        db.commit()

        refreshed = db.execute("SELECT * FROM payments WHERE id=?", (payment_row["id"],)).fetchone()

    item = dict(refreshed)
    try:
        item["metadata"] = json.loads(item["metadata_json"] or "{}")
    except Exception:
        item["metadata"] = {}
    return True, None, item


def _recent_payments(limit=25):
    with conn() as db:
        rows = db.execute(
            """
            SELECT
                p.id,
                p.provider,
                p.provider_payment_id,
                p.provider_checkout_url,
                p.amount,
                p.currency,
                p.status,
                p.destination_ref,
                p.metadata_json,
                p.created_at,
                p.updated_at,
                o.order_code,
                o.source
            FROM payments p
            JOIN orders o ON o.id = p.order_id
            ORDER BY p.id DESC
            LIMIT ?
            """,
            (max(1, min(int(limit or 25), 100)),),
        ).fetchall()

    payments = []
    for row in rows:
        item = dict(row)
        metadata = {}
        if item.get("metadata_json"):
            try:
                metadata = json.loads(item["metadata_json"])
            except Exception:
                metadata = {}
        item["metadata"] = metadata
        payments.append(item)
    return payments


def _mark_webhook_event_processed(provider, event_id):
    event_id = (event_id or "").strip()
    if not event_id:
        return
    with conn() as db:
        db.execute(
            """
            UPDATE webhook_events
            SET processed=1
            WHERE provider=? AND event_id=?
            """,
            (provider, event_id),
        )
        db.commit()

# =========================
# MIGRATE USERS TABLE
# =========================

def migrate_users_table():
    db = conn()
    cols = db.execute("PRAGMA table_info(users)").fetchall()
    colnames = [c["name"] for c in cols]
    if "username" not in colnames:
        print("Adding username column...")
        db.execute("ALTER TABLE users ADD COLUMN username TEXT")
    if "role" not in colnames:
        print("Adding role column...")
        db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    if "is_active" not in colnames:
        print("Adding is_active column...")
        db.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        db.execute("UPDATE users SET is_active=1 WHERE is_active IS NULL")
    if "failed_login_count" not in colnames:
        print("Adding failed_login_count column...")
        db.execute("ALTER TABLE users ADD COLUMN failed_login_count INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE users SET failed_login_count=0 WHERE failed_login_count IS NULL")
    if "locked_until" not in colnames:
        print("Adding locked_until column...")
        db.execute("ALTER TABLE users ADD COLUMN locked_until INTEGER")
    db.commit()
    db.close()

# =========================
# MIGRATE SUBSCRIBERS TABLE
# =========================

def migrate_subscribers_table():
    db = conn()
    cols = db.execute("PRAGMA table_info(subscribers)").fetchall()
    colnames = [c["name"] for c in cols]
    if "weighter" not in colnames:
        print("Adding weighter column to subscribers...")
        db.execute("ALTER TABLE subscribers ADD COLUMN weighter TEXT")
    if "confirmed" not in colnames:
        print("Adding confirmed column to subscribers...")
        db.execute("ALTER TABLE subscribers ADD COLUMN confirmed INTEGER DEFAULT 0")
        db.execute("UPDATE subscribers SET confirmed=0 WHERE confirmed IS NULL")
    if "confirm_token" not in colnames:
        print("Adding confirm_token column to subscribers...")
        db.execute("ALTER TABLE subscribers ADD COLUMN confirm_token TEXT")
    if "unsubscribed" not in colnames:
        print("Adding unsubscribed column to subscribers...")
        db.execute("ALTER TABLE subscribers ADD COLUMN unsubscribed INTEGER NOT NULL DEFAULT 0")
        db.execute("UPDATE subscribers SET unsubscribed=0 WHERE unsubscribed IS NULL")
    if "unsubscribe_token" not in colnames:
        print("Adding unsubscribe_token column to subscribers...")
        db.execute("ALTER TABLE subscribers ADD COLUMN unsubscribe_token TEXT")
    rows_missing_token = db.execute(
        "SELECT id FROM subscribers WHERE unsubscribe_token IS NULL OR unsubscribe_token=''"
    ).fetchall()
    for row in rows_missing_token:
        db.execute(
            "UPDATE subscribers SET unsubscribe_token=? WHERE id=?",
            (uuid.uuid4().hex, row["id"]),
        )
    db.commit()
    db.close()

# =========================
# MIGRATE CONTACT MESSAGES TABLE
# =========================

def migrate_contact_messages_table():
    db = conn()
    cols = db.execute("PRAGMA table_info(contact_messages)").fetchall()
    colnames = [c["name"] for c in cols]
    if "name" not in colnames:
        print("Adding name column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN name TEXT")
    if "recipient_email" not in colnames:
        print("Adding recipient_email column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN recipient_email TEXT")
    if "status" not in colnames:
        print("Adding status column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
    if "emailed_user" not in colnames:
        print("Adding emailed_user column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN emailed_user INTEGER NOT NULL DEFAULT 0")
    if "emailed_admin" not in colnames:
        print("Adding emailed_admin column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN emailed_admin INTEGER NOT NULL DEFAULT 0")
    if "email_status" not in colnames:
        print("Adding email_status column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN email_status TEXT NOT NULL DEFAULT 'pending'")
    if "email_error" not in colnames:
        print("Adding email_error column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN email_error TEXT")
    if "emailed_at" not in colnames:
        print("Adding emailed_at column to contact_messages...")
        db.execute("ALTER TABLE contact_messages ADD COLUMN emailed_at TIMESTAMP")
    db.commit()
    db.close()

# =========================
# MIGRATE USER EMAIL MESSAGES TABLE
# =========================

def migrate_user_email_messages_table():
    db = conn()
    cols = db.execute("PRAGMA table_info(user_email_messages)").fetchall()
    colnames = [c["name"] for c in cols]
    if "status" not in colnames:
        print("Adding status column to user_email_messages...")
        db.execute("ALTER TABLE user_email_messages ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'")
    if "error" not in colnames:
        print("Adding error column to user_email_messages...")
        db.execute("ALTER TABLE user_email_messages ADD COLUMN error TEXT")
    if "sent_at" not in colnames:
        print("Adding sent_at column to user_email_messages...")
        db.execute("ALTER TABLE user_email_messages ADD COLUMN sent_at TIMESTAMP")
    db.commit()
    db.close()

# =========================
# INITIALIZE DATABASE
# =========================

init_db()
migrate_users_table()
migrate_subscribers_table()
migrate_contact_messages_table()
migrate_user_email_messages_table()
with app.app_context():
    db_orm.create_all()

# =========================
# ADMIN LOGIN
# =========================

ADMIN = "admin"
PASSWORD = "admin123"

# Explicit admin dashboard table list.
# Key = label shown in dashboard, value = actual sqlite table name.
DASHBOARD_TABLE_MAP = {
    "users": "users",
    "sqlite_sequence": "sqlite_sequence",
    "subscriptions": "subscriptions",
    "contact_messages": "contact_messages",
    "subscribers": "subscribers",
    "activation_tokens": "activation_tokens",
    "reset_tokens": "reset_tokens",
    "chat_messages": "chat_messages",
    "reset_requests": "reset_requests",
    "shared_files": "shared_files",
    "campaigns": "campaigns",
    "campaign_sends": "campaign_sends",
    "user_email_messages": "user_email_messages",
}


def _existing_table_names():
    db = conn()
    rows = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    db.close()
    return {r["name"] for r in rows}


def _resolve_dashboard_table(table_name):
    if table_name == "user":
        table_name = "users"
    if table_name in DASHBOARD_TABLE_MAP:
        return DASHBOARD_TABLE_MAP[table_name]
    if table_name in DASHBOARD_TABLE_MAP.values():
        return table_name
    return None


def _admin_table_style() -> str:
    return """
    <style>
      body.admin-page {
        font-family: Arial, sans-serif;
        padding: 20px;
      }
      .admin-grid-wrap { overflow-x: auto; max-width: 100%; }
      .admin-grid {
        width: 100%;
        min-width: 1120px;
        border-collapse: collapse;
        table-layout: fixed;
      }
      .admin-grid th,
      .admin-grid td {
        border: 1px solid #bfc6d1;
        padding: 8px 10px;
        vertical-align: top;
        word-break: break-word;
      }
      .admin-grid th {
        height: 52px;
        background: #f4f7fb;
        text-align: left;
      }
      .admin-grid td {
        min-height: 52px;
      }
      .admin-grid td form,
      .admin-form-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .admin-grid input,
      .admin-grid select,
      .admin-form-row input,
      .admin-form-row select {
        width: 160px;
        max-width: 100%;
        min-height: 36px;
        box-sizing: border-box;
      }
      .admin-grid button,
      .admin-form-row button {
        min-height: 36px;
        padding: 0 12px;
      }
      .admin-actions input {
        width: 180px;
        max-width: 100%;
        box-sizing: border-box;
      }
      .admin-actions button { margin-left: 4px; }
      .admin-links {
        margin-top: 16px;
      }
    </style>
    """

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("u") == ADMIN and request.form.get("p") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return """
    <h2>Admin Login</h2>
    <form method=post>
    <input name=u placeholder=user>
    <input name=p type=password placeholder=pass>
    <button>Login</button>
    </form>
    """

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")
    existing = _existing_table_names()
    html = f"""
    {_admin_table_style()}
    <body class="admin-page">
    <h2>Database Tables</h2>
    <div class="admin-grid-wrap">
    <table class="admin-grid">
      <tr><th>Icon</th><th>Table</th><th>View</th><th>Delete</th><th>Status</th></tr>
    """
    icon_map = {
        "users": "👥",
        "subscribers": "👤",
        "subscriptions": "👤",
    }
    for label, actual in DASHBOARD_TABLE_MAP.items():
        exists = actual in existing
        if exists:
            view_link = f"<a href='/view/{label}'>view</a>"
            delete_link = f"<a href='/delete_table/{label}'>delete</a>"
            status = "ok"
        else:
            view_link = "-"
            delete_link = "-"
            status = "missing"
        icon = icon_map.get(label, "🗂")
        html += (
            f"<tr><td style='text-align:center'>{icon}</td><td>{label}</td><td>{view_link}</td><td>{delete_link}</td><td>{status}</td></tr>"
        )
    html += "</table></div><div class='admin-links'><a href='/logout'>logout</a></div></body>"
    return html

# =========================
# VIEW TABLE
# =========================

def _to_int_flag(v, default=1):
    try:
        parsed = int(v)
    except (TypeError, ValueError):
        return default
    return 1 if parsed else 0


def _users_view_html(msg_text="", err_text=""):
    q = (request.args.get("q") or "").strip()
    active = (request.args.get("active") or "").strip()

    where_parts = []
    params = []
    if q:
        like = f"%{q}%"
        where_parts.append("(username LIKE ? OR email LIKE ? OR role LIKE ?)")
        params.extend([like, like, like])
    if active in ("0", "1"):
        where_parts.append("is_active = ?")
        params.append(int(active))

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    db = conn()
    rows = db.execute(
        f"""
        SELECT id, username, email, role, is_active
        FROM users
        {where_sql}
        ORDER BY id DESC
        LIMIT 500
        """,
        params,
    ).fetchall()
    db.close()

    msg_html = f"<div style='color:#14532d'>{html_escape(msg_text)}</div>" if msg_text else ""
    err_html = f"<div style='color:#991b1b'>{html_escape(err_text)}</div>" if err_text else ""

    html = f"""
    {_admin_table_style()}
    <body class="admin-page">
    <h2>users</h2>
    {msg_html}
    {err_html}
    <h3>Select (filter)</h3>
    <form method="get" action="/view/users" class="admin-form-row">
      <input name="q" placeholder="search username/email/role" value="{html_escape(q)}">
      <select name="active">
        <option value="" {"selected" if active == "" else ""}>all</option>
        <option value="1" {"selected" if active == "1" else ""}>active</option>
        <option value="0" {"selected" if active == "0" else ""}>inactive</option>
      </select>
      <button type="submit">select</button>
      <a href="/view/users">reset</a>
    </form>
    <h3>Add user</h3>
    <form method="post" action="/view/users" class="admin-form-row">
      <input type="hidden" name="action" value="add">
      <input name="username" placeholder="username" required>
      <input name="email" placeholder="email" required>
      <input name="password" type="password" placeholder="password" required>
      <input name="role" placeholder="role (user/admin)" value="user">
      <select name="is_active">
        <option value="1" selected>active</option>
        <option value="0">inactive</option>
      </select>
      <button type="submit">add</button>
    </form>
    <h3>Users</h3>
    <div class="admin-grid-wrap">
    <table class="admin-grid">
      <tr><th>id</th><th>username</th><th>email</th><th>role</th><th>is_active</th><th>modify</th><th>delete</th></tr>
    """

    for r in rows:
        rid = int(r["id"])
        username = html_escape(str(r["username"] or ""))
        email = html_escape(str(r["email"] or ""))
        role = html_escape(str(r["role"] or "user"))
        is_active = int(r["is_active"] or 0)
        html += f"""
        <tr>
          <td>{rid}</td>
          <td>{username}</td>
          <td>{email}</td>
          <td>{role}</td>
          <td>{is_active}</td>
          <td>
            <form method="post" action="/view/users">
              <input type="hidden" name="action" value="modify">
              <input type="hidden" name="id" value="{rid}">
              <input name="username" value="{username}" required>
              <input name="email" value="{email}" required>
              <input name="role" value="{role}">
              <select name="is_active">
                <option value="1" {"selected" if is_active == 1 else ""}>1</option>
                <option value="0" {"selected" if is_active == 0 else ""}>0</option>
              </select>
              <input name="password" type="password" placeholder="new password (optional)">
              <button type="submit">modify</button>
            </form>
          </td>
          <td>
            <form method="post" action="/view/users" onsubmit="return confirm('Delete user id {rid}?');">
              <input type="hidden" name="action" value="delete">
              <input type="hidden" name="id" value="{rid}">
              <button type="submit">delete</button>
            </form>
          </td>
        </tr>
        """

    html += "</table></div><div class='admin-links'><a href='/dashboard'>back</a></div></body>"
    return html


def _table_exists(table_name):
    with conn() as db:
        row = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
    return bool(row)


def _table_columns(table_name):
    with conn() as db:
        cols = db.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return cols


def _pk_column_name(columns):
    for c in columns:
        if int(c["pk"] or 0) > 0:
            return c["name"]
    return None


def _coerce_sql_value(raw_value, col_type):
    if raw_value is None:
        return None
    v = str(raw_value).strip()
    if v == "":
        return None
    t = (col_type or "").upper()
    if "INT" in t:
        try:
            return int(v)
        except ValueError:
            return v
    if any(x in t for x in ("REAL", "FLOA", "DOUB")):
        try:
            return float(v)
        except ValueError:
            return v
    return v


def _generic_table_view_html(table_name, msg_text="", err_text=""):
    q = (request.args.get("q") or "").strip()
    columns = _table_columns(table_name)
    if not columns:
        return f"<h2>{table_name}</h2><p>No columns found.</p><a href='/dashboard'>back</a>"

    pk_col = _pk_column_name(columns)
    auto_pk = None
    if pk_col:
        for c in columns:
            if c["name"] == pk_col and "INT" in (c["type"] or "").upper():
                auto_pk = pk_col
                break

    where_sql = ""
    params = []
    if q:
        searchable = [c["name"] for c in columns]
        where_sql = " WHERE " + " OR ".join([f'CAST("{c}" AS TEXT) LIKE ?' for c in searchable])
        params = [f"%{q}%"] * len(searchable)

    with conn() as db:
        rows = db.execute(
            f'SELECT rowid as __rowid__, * FROM "{table_name}"{where_sql} ORDER BY __rowid__ DESC LIMIT 300',
            params,
        ).fetchall()

    msg_html = f"<div style='color:#14532d'>{html_escape(msg_text)}</div>" if msg_text else ""
    err_html = f"<div style='color:#991b1b'>{html_escape(err_text)}</div>" if err_text else ""

    html = f"""
    {_admin_table_style()}
    <body class="admin-page">
    <h2>{html_escape(table_name)}</h2>
    {msg_html}
    {err_html}
    <h3>Select (filter)</h3>
    <form method="get" action="/view/{html_escape(table_name)}" class="admin-actions">
      <input name="q" placeholder="search in all columns" value="{html_escape(q)}">
      <button type="submit">select</button>
      <a href="/view/{html_escape(table_name)}">reset</a>
    </form>
    <h3>Add row</h3>
    <form method="post" action="/view/{html_escape(table_name)}" class="admin-actions">
      <input type="hidden" name="action" value="add">
    """

    for c in columns:
        col_name = c["name"]
        if auto_pk and col_name == auto_pk:
            continue
        required = bool(int(c["notnull"] or 0)) and c["dflt_value"] is None
        req_attr = "required" if required else ""
        html += (
            f'<input name="f_{html_escape(col_name)}" '
            f'placeholder="{html_escape(col_name)} ({html_escape(c["type"] or "TEXT")})" {req_attr}> '
        )
    html += "<button type='submit'>add</button></form>"

    table_cols = [c["name"] for c in columns]
    html += "<h3>Rows</h3><div class='admin-grid-wrap'><table class='admin-grid'><tr>"
    for c in table_cols:
        html += f"<th>{html_escape(c)}</th>"
    html += "<th>modify</th><th>delete</th></tr>"

    for r in rows:
        html += "<tr>"
        for c in table_cols:
            html += f"<td>{html_escape(str(r[c]) if r[c] is not None else '')}</td>"

        html += f"<td><form method='post' action='/view/{html_escape(table_name)}' class='admin-actions'>"
        html += "<input type='hidden' name='action' value='modify'>"
        if pk_col:
            html += f"<input type='hidden' name='__pk_col' value='{html_escape(pk_col)}'>"
            html += f"<input type='hidden' name='__pk_val' value='{html_escape(str(r[pk_col]))}'>"
        else:
            html += "<input type='hidden' name='__pk_col' value=''>"
            html += f"<input type='hidden' name='__rowid' value='{html_escape(str(r['__rowid__']))}'>"

        for c in columns:
            col_name = c["name"]
            if auto_pk and col_name == auto_pk:
                continue
            val = "" if r[col_name] is None else str(r[col_name])
            html += (
                f'<input name="f_{html_escape(col_name)}" '
                f'value="{html_escape(val)}" '
                f'placeholder="{html_escape(col_name)}"> '
            )
        html += "<button type='submit'>modify</button></form></td>"

        html += (
            f"<td><form method='post' action='/view/{html_escape(table_name)}' class='admin-actions' "
            "onsubmit=\"return confirm('Delete this row?');\">"
        )
        html += "<input type='hidden' name='action' value='delete'>"
        if pk_col:
            html += f"<input type='hidden' name='__pk_col' value='{html_escape(pk_col)}'>"
            html += f"<input type='hidden' name='__pk_val' value='{html_escape(str(r[pk_col]))}'>"
        else:
            html += "<input type='hidden' name='__pk_col' value=''>"
            html += f"<input type='hidden' name='__rowid' value='{html_escape(str(r['__rowid__']))}'>"
        html += "<button type='submit'>delete</button></form></td>"
        html += "</tr>"

    html += "</table></div><div class='admin-links'><a href='/dashboard'>back</a></div></body>"
    return html


def _handle_generic_table_post(table_name):
    action = (request.form.get("action") or "").strip().lower()
    columns = _table_columns(table_name)
    if not columns:
        return ("no_columns", "missing_schema")
    pk_col = _pk_column_name(columns)
    auto_pk = None
    if pk_col:
        for c in columns:
            if c["name"] == pk_col and "INT" in (c["type"] or "").upper():
                auto_pk = pk_col
                break

    col_meta = {c["name"]: c for c in columns}
    editable_cols = [c["name"] for c in columns if not (auto_pk and c["name"] == auto_pk)]

    if action == "add":
        insert_cols = []
        insert_vals = []
        for c in editable_cols:
            form_key = f"f_{c}"
            if form_key not in request.form:
                continue
            insert_cols.append(c)
            insert_vals.append(_coerce_sql_value(request.form.get(form_key), col_meta[c]["type"]))
        if not insert_cols:
            return ("missing_fields", "add_failed")
        marks = ",".join(["?"] * len(insert_cols))
        cols_sql = ",".join([f'"{c}"' for c in insert_cols])
        with conn() as db:
            db.execute(f'INSERT INTO "{table_name}" ({cols_sql}) VALUES ({marks})', insert_vals)
            db.commit()
        return ("row_added", "")

    if action == "modify":
        set_parts = []
        set_vals = []
        for c in editable_cols:
            form_key = f"f_{c}"
            if form_key not in request.form:
                continue
            set_parts.append(f'"{c}"=?')
            set_vals.append(_coerce_sql_value(request.form.get(form_key), col_meta[c]["type"]))
        if not set_parts:
            return ("missing_fields", "modify_failed")

        pk_name = (request.form.get("__pk_col") or "").strip()
        if pk_name:
            pk_val = request.form.get("__pk_val")
            if pk_val is None:
                return ("invalid_pk", "modify_failed")
            if pk_name in col_meta:
                pk_val = _coerce_sql_value(pk_val, col_meta[pk_name]["type"])
            set_vals.append(pk_val)
            with conn() as db:
                db.execute(
                    f'UPDATE "{table_name}" SET {",".join(set_parts)} WHERE "{pk_name}"=?',
                    set_vals,
                )
                db.commit()
            return ("row_modified", "")

        rowid = request.form.get("__rowid")
        if not rowid:
            return ("invalid_rowid", "modify_failed")
        set_vals.append(int(rowid))
        with conn() as db:
            db.execute(
                f'UPDATE "{table_name}" SET {",".join(set_parts)} WHERE rowid=?',
                set_vals,
            )
            db.commit()
        return ("row_modified", "")

    if action == "delete":
        pk_name = (request.form.get("__pk_col") or "").strip()
        if pk_name:
            pk_val = request.form.get("__pk_val")
            if pk_val is None:
                return ("invalid_pk", "delete_failed")
            if pk_name in col_meta:
                pk_val = _coerce_sql_value(pk_val, col_meta[pk_name]["type"])
            with conn() as db:
                db.execute(f'DELETE FROM "{table_name}" WHERE "{pk_name}"=?', (pk_val,))
                db.commit()
            return ("row_deleted", "")

        rowid = request.form.get("__rowid")
        if not rowid:
            return ("invalid_rowid", "delete_failed")
        with conn() as db:
            db.execute(f'DELETE FROM "{table_name}" WHERE rowid=?', (int(rowid),))
            db.commit()
        return ("row_deleted", "")

    return ("invalid_action", "invalid_action")


@app.route("/view/<table>", methods=["GET", "POST"])
def view(table):
    if not session.get("ok"):
        return redirect("/")
    resolved = _resolve_dashboard_table(table)
    if not resolved:
        return "table not allowed", 400

    if resolved == "users":
        if request.method == "POST":
            action = (request.form.get("action") or "").strip().lower()
            try:
                if action == "add":
                    username = (request.form.get("username") or "").strip()
                    email = (request.form.get("email") or "").strip()
                    password = request.form.get("password") or ""
                    role = (request.form.get("role") or "user").strip() or "user"
                    is_active = _to_int_flag(request.form.get("is_active"), default=1)
                    if not username or not email or not password:
                        return redirect("/view/users?err=missing+required+fields")
                    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    db = conn()
                    db.execute(
                        "INSERT INTO users(username,email,password,role,is_active) VALUES(?,?,?,?,?)",
                        (username, email, hashed, role, is_active),
                    )
                    db.commit()
                    db.close()
                    return redirect("/view/users?msg=user+added")
                if action == "modify":
                    user_id = int(request.form.get("id") or "0")
                    if user_id <= 0:
                        return redirect("/view/users?err=invalid+id")
                    username = (request.form.get("username") or "").strip()
                    email = (request.form.get("email") or "").strip()
                    role = (request.form.get("role") or "user").strip() or "user"
                    password = request.form.get("password") or ""
                    is_active = _to_int_flag(request.form.get("is_active"), default=1)
                    if not username or not email:
                        return redirect("/view/users?err=username+and+email+required")
                    db = conn()
                    if password.strip():
                        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                        db.execute(
                            """
                            UPDATE users
                            SET username=?, email=?, role=?, is_active=?, password=?
                            WHERE id=?
                            """,
                            (username, email, role, is_active, hashed, user_id),
                        )
                    else:
                        db.execute(
                            """
                            UPDATE users
                            SET username=?, email=?, role=?, is_active=?
                            WHERE id=?
                            """,
                            (username, email, role, is_active, user_id),
                        )
                    db.commit()
                    db.close()
                    return redirect("/view/users?msg=user+modified")
                if action == "delete":
                    user_id = int(request.form.get("id") or "0")
                    if user_id <= 0:
                        return redirect("/view/users?err=invalid+id")
                    db = conn()
                    db.execute("DELETE FROM users WHERE id=?", (user_id,))
                    db.commit()
                    db.close()
                    return redirect("/view/users?msg=user+deleted")
                return redirect("/view/users?err=invalid+action")
            except sqlite3.IntegrityError:
                return redirect("/view/users?err=user+already+exists")
            except Exception as e:
                return redirect(f"/view/users?err={html_escape(str(e))}")

        return _users_view_html(
            msg_text=(request.args.get("msg") or "").strip(),
            err_text=(request.args.get("err") or "").strip(),
        )

    if not _table_exists(resolved):
        return f"table '{resolved}' not found", 404
    if request.method == "POST":
        try:
            msg_code, err_code = _handle_generic_table_post(resolved)
            if err_code:
                return redirect(f"/view/{resolved}?err={err_code}")
            return redirect(f"/view/{resolved}?msg={msg_code}")
        except sqlite3.IntegrityError:
            return redirect(f"/view/{resolved}?err=integrity_error")
        except Exception as e:
            return redirect(f"/view/{resolved}?err={html_escape(str(e))}")

    return _generic_table_view_html(
        resolved,
        msg_text=(request.args.get("msg") or "").strip(),
        err_text=(request.args.get("err") or "").strip(),
    )

# =========================
# DELETE TABLE
# =========================

@app.route("/delete_table/<table>")
def delete_table(table):
    if not session.get("ok"):
        return redirect("/")
    resolved = _resolve_dashboard_table(table)
    if not resolved:
        return "table not allowed", 400
    db = conn()
    exists = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (resolved,),
    ).fetchone()
    if not exists:
        db.close()
        return f"table '{resolved}' not found", 404
    db.execute(f'DROP TABLE "{resolved}"')
    db.commit()
    db.close()
    return redirect("/dashboard")

# =========================
# API REGISTER
# =========================

def _send_email_via_sendgrid_api(to_email, subject, html_body):
    api_key = (os.getenv("SENDGRID_API_KEY") or "").strip()
    from_email = (
        os.getenv("SENDGRID_FROM_EMAIL")
        or os.getenv("MAIL_DEFAULT_SENDER")
        or os.getenv("SMTP_FROM")
        or os.getenv("SMTP_USER")
        or "no-reply@localhost"
    )
    if not api_key:
        print("SENDGRID_API_KEY missing; cannot use API provider mode.")
        return False

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_body}],
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=20) as resp:
            return 200 <= int(resp.status) < 300
    except urllib_error.HTTPError as e:
        print("SendGrid HTTP error:", e.code)
        return False
    except Exception as e:
        print("SendGrid send failed:", e)
        return False


def _send_email_via_mailgun_api(to_email, subject, html_body):
    api_key = (os.getenv("MAILGUN_API_KEY") or "").strip()
    domain = (os.getenv("MAILGUN_DOMAIN") or "").strip()
    from_email = (
        os.getenv("MAILGUN_FROM_EMAIL")
        or os.getenv("MAIL_DEFAULT_SENDER")
        or os.getenv("SMTP_FROM")
        or os.getenv("SMTP_USER")
        or f"mailgun@{domain or 'localhost'}"
    )
    if not api_key or not domain:
        print("MAILGUN_API_KEY/MAILGUN_DOMAIN missing; cannot use Mailgun provider mode.")
        return False

    endpoint = f"https://api.mailgun.net/v3/{domain}/messages"
    form = urlencode(
        {
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_body,
        }
    ).encode("utf-8")
    auth_token = base64.b64encode(f"api:{api_key}".encode("utf-8")).decode("utf-8")
    req = urllib_request.Request(
        endpoint,
        data=form,
        method="POST",
        headers={
            "Authorization": f"Basic {auth_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib_request.urlopen(req, timeout=20) as resp:
            return 200 <= int(resp.status) < 300
    except urllib_error.HTTPError as e:
        print("Mailgun HTTP error:", e.code)
        return False
    except Exception as e:
        print("Mailgun send failed:", e)
        return False


def _send_email_via_flask_mail(to_email, subject, html_body):
    if not app.config.get("MAIL_SERVER"):
        print("MAIL_SERVER not configured; skipping Flask-Mail send.")
        return False
    try:
        msg = Message(subject=subject, recipients=[to_email], html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print("Flask-Mail send failed:", e)
        return False


def _send_email_via_smtp(to_email, subject, html_body):
    host = os.getenv("MAIL_SERVER") or os.getenv("SMTP_HOST")
    port = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT", "587"))
    user = os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USER")
    password = os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASS")
    from_email = (
        os.getenv("MAIL_DEFAULT_SENDER")
        or os.getenv("SMTP_FROM")
        or user
        or "no-reply@localhost"
    )
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    if not host:
        print("SMTP not configured; skipping email send.")
        return False
    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content("This email requires an HTML-capable client.")
    msg.add_alternative(html_body, subtype="html")
    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
        with server:
            if use_tls and not use_ssl:
                server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print("SMTP send failed:", e)
        return False


def _resolve_email_provider():
    # auto mode: Flask-Mail for dev/testing, API provider for production.
    if EMAIL_PROVIDER and EMAIL_PROVIDER != "auto":
        return EMAIL_PROVIDER
    if APP_ENV in ("production", "prod", "live"):
        if os.getenv("SENDGRID_API_KEY"):
            return "sendgrid"
        if os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN"):
            return "mailgun"
        return "smtp"
    return "flask_mail"


def send_email(to_email, subject, html_body):
    provider = _resolve_email_provider()
    if provider in ("api", "sendgrid"):
        return _send_email_via_sendgrid_api(to_email, subject, html_body)
    if provider == "mailgun":
        return _send_email_via_mailgun_api(to_email, subject, html_body)
    if provider == "smtp":
        return _send_email_via_smtp(to_email, subject, html_body)
    # Default: Flask-Mail for local/small testing.
    return _send_email_via_flask_mail(to_email, subject, html_body)


def _email_provider_failure_message():
    provider = _resolve_email_provider()
    if provider in ("api", "sendgrid"):
        return "Email send failed through SendGrid. Check sender verification and API key permissions."
    if provider == "mailgun":
        return "Email send failed through Mailgun. Check domain authentication and API key settings."
    if provider == "smtp":
        return "Email send failed through SMTP. Check SMTP settings and network access."
    return "Email send failed through the configured mail provider."


def validate_email_runtime_config():
    mail_server = app.config.get("MAIL_SERVER") or ""
    mail_port = int(app.config.get("MAIL_PORT") or 0)
    mail_user = app.config.get("MAIL_USERNAME") or ""
    mail_pass = app.config.get("MAIL_PASSWORD") or ""
    mail_sender = app.config.get("MAIL_DEFAULT_SENDER") or ""
    provider = _resolve_email_provider()

    if provider in ("smtp", "flask_mail"):
        if not mail_server:
            print("EMAIL CONFIG WARNING: MAIL_SERVER/SMTP_HOST is missing.")
        if not mail_port:
            print("EMAIL CONFIG WARNING: MAIL_PORT/SMTP_PORT is missing or invalid.")
        if not mail_user:
            print("EMAIL CONFIG WARNING: MAIL_USERNAME/SMTP_USER is missing.")
        if not mail_pass:
            print("EMAIL CONFIG WARNING: MAIL_PASSWORD/SMTP_PASS is missing.")
        if not mail_sender:
            print("EMAIL CONFIG WARNING: MAIL_DEFAULT_SENDER (or SMTP_FROM) is missing.")
        if mail_port in (25, 587):
            print(
                "EMAIL NOTE: port 25/587 can be blocked by some hosting providers. "
                "If sends fail, verify outbound SMTP port policy."
            )
        if "gmail.com" in mail_server.lower() or "google" in mail_server.lower():
            print(
                "EMAIL NOTE: Gmail SMTP usually requires an App Password "
                "(not your normal account password)."
            )
    elif provider in ("api", "sendgrid"):
        if not (os.getenv("SENDGRID_API_KEY") or "").strip():
            print("EMAIL CONFIG WARNING: SENDGRID_API_KEY is missing.")
        if not (
            (os.getenv("SENDGRID_FROM_EMAIL") or "").strip()
            or mail_sender
            or (os.getenv("SMTP_FROM") or "").strip()
        ):
            print("EMAIL CONFIG WARNING: SENDGRID_FROM_EMAIL or MAIL_DEFAULT_SENDER is missing.")
    elif provider == "mailgun":
        if not (os.getenv("MAILGUN_API_KEY") or "").strip():
            print("EMAIL CONFIG WARNING: MAILGUN_API_KEY is missing.")
        if not (os.getenv("MAILGUN_DOMAIN") or "").strip():
            print("EMAIL CONFIG WARNING: MAILGUN_DOMAIN is missing.")
        if not (
            (os.getenv("MAILGUN_FROM_EMAIL") or "").strip()
            or mail_sender
            or (os.getenv("SMTP_FROM") or "").strip()
        ):
            print("EMAIL CONFIG WARNING: MAILGUN_FROM_EMAIL or MAIL_DEFAULT_SENDER is missing.")


def build_activation_email(username, token):
    link = f"{PUBLIC_BASE_URL}/activate?token={token}"
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>Welcome to TheGhost App</h2>
      <p>Hi {username}, thanks for registering.</p>
      <p>Click the link to activate your account:</p>
      <p><a href="{link}">{link}</a></p>
      <p>If you did not register, you can ignore this email.</p>
    </div>
    """


def build_newsletter_email(username):
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>Thanks for subscribing</h2>
      <p>Hi {username},</p>
      <p>Thank you for subscribing to the newsletter.</p>
      <p>You'll receive news soon.</p>
    </div>
    """

def build_subscriber_confirm_email(username, token):
    link = f"{PUBLIC_BASE_URL}/confirm?token={token}"
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>Confirm your subscription</h2>
      <p>Hi {username},</p>
      <p>Please confirm your newsletter subscription by clicking this link:</p>
      <p><a href="{link}">{link}</a></p>
      <p>If you did not request this, you can ignore this email.</p>
    </div>
    """

def build_boxletter_notice(username, email, weighter):
    note_html = ""
    if weighter:
        note_html = f"<p>Message: {weighter}</p>"
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>New Newsletter Subscription</h2>
      <p>Name: {username}</p>
      <p>Email: {email}</p>
      {note_html}
    </div>
    """


def build_reset_email(token):
    link = f"{PUBLIC_BASE_URL}/reset-password?token={token}"
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>Password Reset</h2>
      <p>Click the link below to reset your password:</p>
      <p><a href="{link}">{link}</a></p>
      <p>If you did not request a reset, ignore this email.</p>
    </div>
    """


def build_contact_forward_email(username, from_email, message):
    safe_user = html_escape(username or "")
    safe_from = html_escape(from_email or "")
    safe_message = html_escape(message or "").replace("\n", "<br>")
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>New Contact Message</h2>
      <p><strong>From user:</strong> {safe_user}</p>
      <p><strong>From email:</strong> {safe_from}</p>
      <p><strong>Message:</strong><br>{safe_message}</p>
    </div>
    """


def build_contact_admin_email(name, from_email, message):
    safe_name = html_escape(name or "")
    safe_from = html_escape(from_email or "")
    safe_message = html_escape(message or "").replace("\n", "<br>")
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>New Contact Message</h2>
      <p><strong>Name:</strong> {safe_name}</p>
      <p><strong>Email:</strong> {safe_from}</p>
      <p><strong>Message:</strong><br>{safe_message}</p>
    </div>
    """


def build_contact_user_ack_email(name):
    safe_name = html_escape(name or "there")
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <h2>Thanks, we got it</h2>
      <p>Hi {safe_name},</p>
      <p>Your message has been received. We will reply as soon as possible.</p>
      <p>— TheGhost Team</p>
    </div>
    """


def create_reset_request(email):
    """
    Store reset request in DB and send reset email when account exists.
    Returns dict with generic success response for security.
    """
    if not email:
        return {"success": False, "error": "Email required", "status_code": 400}

    db = conn()
    user = db.execute("SELECT email FROM users WHERE email=?", (email,)).fetchone()
    if not user:
        db.close()
        # Generic success: do not disclose account existence
        return {"success": True, "message": "If the account exists, a reset email has been sent.", "status_code": 200}

    token = uuid.uuid4().hex
    db.execute("INSERT INTO reset_tokens(email, token) VALUES(?,?)", (email, token))
    db.execute(
        "INSERT INTO email_tokens(email, token, purpose) VALUES(?,?,?)",
        (email, token, "reset_password"),
    )
    db.execute(
        "INSERT INTO reset_requests(email, token, status) VALUES(?,?,?)",
        (email, token, "requested"),
    )
    db.commit()
    db.close()

    sent = send_email(email, "Reset your TheGhost password", build_reset_email(token))
    if sent:
        with conn() as db2:
            db2.execute(
                "UPDATE reset_requests SET status='emailed', emailed_at=CURRENT_TIMESTAMP WHERE token=?",
                (token,),
            )
    return {"success": True, "message": "If the account exists, a reset email has been sent.", "status_code": 200}


def _ensure_subscriber_for_user(username, email):
    if not username or not email:
        return
    with conn() as db:
        row = db.execute(
            "SELECT id, unsubscribe_token FROM subscribers WHERE email=?",
            (email,),
        ).fetchone()
        if row:
            unsub_token = row["unsubscribe_token"] or uuid.uuid4().hex
            db.execute(
                """
                UPDATE subscribers
                SET username=?, confirmed=1, confirm_token=NULL, unsubscribed=0, unsubscribe_token=?
                WHERE id=?
                """,
                (username, unsub_token, row["id"]),
            )
        else:
            db.execute(
                """
                INSERT INTO subscribers(username,email,weighter,confirmed,confirm_token,unsubscribed,unsubscribe_token)
                VALUES(?,?,?,?,?,?,?)
                """,
                (username, email, "user-register", 1, None, 0, uuid.uuid4().hex),
            )


def _sync_users_to_subscribers():
    inserted = 0
    updated = 0

    with conn() as db:
        try:
            users = db.execute(
                """
                SELECT username, email
                FROM users
                WHERE COALESCE(email, '') <> ''
                  AND COALESCE(is_active, 1) = 1
                ORDER BY id ASC
                """
            ).fetchall()
        except sqlite3.OperationalError:
            users = db.execute(
                """
                SELECT username, email
                FROM users
                WHERE COALESCE(email, '') <> ''
                ORDER BY id ASC
                """
            ).fetchall()

        for row in users:
            username = (row["username"] or "user").strip()
            email = (row["email"] or "").strip().lower()
            if not email:
                continue

            existing = db.execute(
                "SELECT id, unsubscribed, unsubscribe_token FROM subscribers WHERE email=?",
                (email,),
            ).fetchone()

            if existing:
                db.execute(
                    """
                    UPDATE subscribers
                    SET username=COALESCE(NULLIF(?, ''), username),
                        unsubscribe_token=COALESCE(NULLIF(unsubscribe_token,''), ?)
                    WHERE id=?
                    """,
                    (username, uuid.uuid4().hex, existing["id"]),
                )
                updated += 1
                continue

            db.execute(
                """
                INSERT INTO subscribers(username,email,weighter,confirmed,confirm_token,unsubscribed,unsubscribe_token)
                VALUES(?,?,?,?,?,?,?)
                """,
                (username, email, "user-sync", 1, None, 0, uuid.uuid4().hex),
            )
            inserted += 1

        db.commit()

    return {"inserted": inserted, "updated": updated}


def _new_raw_token():
    return secrets.token_urlsafe(32)


def _hash_token(raw_token):
    return hashlib.sha256(f"{TOKEN_PEPPER}:{raw_token}".encode("utf-8")).hexdigest()


def _find_user_for_activation_token(raw_token):
    token_hash = _hash_token(raw_token)
    with conn() as db:
        # Preferred path: hashed token lookup.
        row = db.execute(
            """
            SELECT id, email FROM activation_tokens
            WHERE token=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (token_hash,),
        ).fetchone()
        if row:
            return row["id"], row["email"]

        # Legacy fallback: old rows may still store raw token.
        legacy = db.execute(
            """
            SELECT id, email, token FROM activation_tokens
            ORDER BY id DESC
            """,
        ).fetchall()
    for r in legacy:
        candidate = r["token"] or ""
        if hmac.compare_digest(candidate, raw_token):
            return r["id"], r["email"]
    return None, None


def _get_user_identity(email):
    with conn() as db:
        row = db.execute(
            "SELECT username, email FROM users WHERE email=?",
            (email,),
        ).fetchone()
    return row


def _issue_activation_token(email):
    raw_token = _new_raw_token()
    token_hash = _hash_token(raw_token)
    with conn() as db:
        db.execute(
            "INSERT INTO activation_tokens(email, token) VALUES(?,?)",
            (email, token_hash),
        )
        db.execute(
            "INSERT INTO email_tokens(email, token, purpose) VALUES(?,?,?)",
            (email, token_hash, "activation"),
        )
        db.commit()
    return raw_token


def _registration_email_workflow(username, email):
    db_user = _get_user_identity(email)
    if not db_user:
        return None
    safe_username = (db_user["username"] or username or "user").strip()
    safe_email = (db_user["email"] or email).strip().lower()

    token = _issue_activation_token(safe_email)
    send_email(safe_email, "Activate your TheGhost account", build_activation_email(safe_username, token))
    _ensure_subscriber_for_user(safe_username, safe_email)
    send_email(safe_email, "Welcome to the newsletter", build_newsletter_email(safe_username))
    return token


def _resend_activation_if_inactive(email, username_fallback="user"):
    with conn() as db:
        user = db.execute(
            "SELECT username, is_active FROM users WHERE email=?",
            (email,),
        ).fetchone()
    if not user:
        return False
    if int(user["is_active"] or 0) == 1:
        return False
    username = (user["username"] or username_fallback or "user").strip()
    token = _issue_activation_token(email)
    send_email(email, "Activate your TheGhost account", build_activation_email(username, token))
    return True


def sanitize_next_url(next_url):
    default_next = f"{STATIC_BASE_URL}/index.html"
    if not next_url:
        return default_next

    static_prefix = STATIC_BASE_URL.rstrip("/") + "/"
    request_prefix = request.host_url.rstrip("/") + "/"
    if next_url.startswith(static_prefix) or next_url.startswith(request_prefix):
        return next_url
    return default_next


@app.route("/register", methods=["POST"])
def register_form():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    next_url = sanitize_next_url(request.form.get("next"))
    if not username or not email or not password:
        return redirect(f"{next_url}?register=failed")
    try:
        db = conn()
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.execute(
            "INSERT INTO users(username,email,password,role,is_active) VALUES(?,?,?,?,?)",
            (username, email, hashed, "user", 0)
        )
        db.commit()
        db.close()
        _registration_email_workflow(username, email)
        return redirect(f"{next_url}?register=ok")
    except sqlite3.IntegrityError:
        resent = _resend_activation_if_inactive(email, username_fallback=username)
        if resent:
            return redirect(f"{next_url}?register=pending_activation")
        return redirect(f"{next_url}?register=exists")
    except Exception as e:
        print(e)
        return redirect(f"{next_url}?register=failed")


def _activate_account_by_token(token):
    token_id, email = _find_user_for_activation_token(token)
    if not token_id or not email:
        return False
    with conn() as db:
        db.execute("UPDATE users SET is_active=1 WHERE email=?", (email,))
        db.execute("DELETE FROM activation_tokens WHERE id=?", (token_id,))
        db.execute("DELETE FROM email_tokens WHERE email=? AND purpose='activation'", (email,))
        db.commit()
    return True


@app.route("/activate/<token>", methods=["GET"])
def activate_account(token):
    ok = _activate_account_by_token(token)
    if not ok:
        return redirect(f"{STATIC_BASE_URL}/index.html?activate=invalid")
    return redirect(f"{STATIC_BASE_URL}/index.html?activate=ok&login=ready")


@app.route("/activate", methods=["GET"])
def activate_account_query():
    token = (request.args.get("token") or "").strip()
    if not token:
        return redirect(f"{STATIC_BASE_URL}/index.html?activate=invalid")
    ok = _activate_account_by_token(token)
    if not ok:
        return redirect(f"{STATIC_BASE_URL}/index.html?activate=invalid")
    return redirect(f"{STATIC_BASE_URL}/index.html?activate=ok&login=ready")


@app.route("/resend-activation", methods=["POST"])
def resend_activation():
    payload = request.get_json(silent=True) if request.is_json else request.form
    payload = payload or {}
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return jsonify(success=False, error="Email required"), 400

    with conn() as db:
        user = db.execute(
            "SELECT username, email, is_active FROM users WHERE email=?",
            (email,),
        ).fetchone()
    if not user:
        return jsonify(success=True, message="If account exists, activation email has been sent")
    if int(user["is_active"] or 0) == 1:
        return jsonify(success=True, message="Account already active")

    token = _issue_activation_token(user["email"])
    send_email(
        user["email"],
        "Activate your TheGhost account",
        build_activation_email(user["username"] or "user", token),
    )
    return jsonify(success=True, message="Activation email sent")


@app.route("/request-reset", methods=["POST"])
def request_reset_form():
    email = request.form.get("email")
    next_url = sanitize_next_url(request.form.get("next"))
    result = create_reset_request(email)
    if not result["success"]:
        return redirect(f"{next_url}?reset=failed")
    return redirect(f"{next_url}?reset=sent")


@app.route("/api/request-reset", methods=["POST"])
def request_reset_api():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    result = create_reset_request(email)
    if not result["success"]:
        return jsonify(success=False, error=result["error"]), result["status_code"]
    return jsonify(success=True, message=result["message"]), 200


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    if request.is_json:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        result = create_reset_request(email)
        if not result["success"]:
            return jsonify(success=False, error=result["error"]), result["status_code"]
        return jsonify(success=True, message=result["message"]), 200

    email = (request.form.get("email") or "").strip().lower()
    next_url = sanitize_next_url(request.form.get("next"))
    result = create_reset_request(email)
    if not result["success"]:
        return redirect(f"{next_url}?reset=failed")
    return redirect(f"{next_url}?reset=sent")


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "GET":
        return f"""
        <h2>Reset Password</h2>
        <form method="POST">
          <input type="password" name="password" placeholder="New password" required />
          <input type="password" name="confirm" placeholder="Confirm password" required />
          <button type="submit">Reset</button>
        </form>
        """

    password = request.form.get("password")
    confirm = request.form.get("confirm")
    if not password or password != confirm:
        return "<p>Passwords do not match.</p>"

    db = conn()
    row = db.execute("SELECT email FROM reset_tokens WHERE token=?", (token,)).fetchone()
    if not row:
        db.close()
        return "<p>Invalid or expired token.</p>"
    email = row["email"]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    db.execute("DELETE FROM reset_tokens WHERE token=?", (token,))
    db.execute("DELETE FROM email_tokens WHERE token=? AND purpose='reset_password'", (token,))
    db.commit()
    db.close()
    return "<p>Password updated. You can close this page.</p>"


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password_query():
    if request.method == "GET":
        token = (request.args.get("token") or "").strip()
        if not token:
            return "<p>Missing token.</p>", 400
        return redirect(f"/reset/{token}")

    payload = request.get_json(silent=True) if request.is_json else request.form
    payload = payload or {}
    token = (payload.get("token") or "").strip()
    password = payload.get("password") or ""
    confirm = payload.get("confirm") or payload.get("password_confirm") or password

    if not token or not password or password != confirm:
        if request.is_json:
            return jsonify(success=False, error="Invalid token or password mismatch"), 400
        return "<p>Invalid token or password mismatch.</p>", 400

    db = conn()
    row = db.execute("SELECT email FROM reset_tokens WHERE token=?", (token,)).fetchone()
    if not row:
        db.close()
        if request.is_json:
            return jsonify(success=False, error="Invalid or expired token"), 400
        return "<p>Invalid or expired token.</p>", 400

    email = row["email"]
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    db.execute("DELETE FROM reset_tokens WHERE token=?", (token,))
    db.execute("DELETE FROM email_tokens WHERE token=? AND purpose='reset_password'", (token,))
    db.commit()
    db.close()

    if request.is_json:
        return jsonify(success=True, message="Password updated"), 200
    return "<p>Password updated. You can close this page.</p>"

@app.route("/api/register", methods=["POST"])
def register():
    print("REGISTER ENDPOINT HIT")
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        return jsonify(success=False, error="Missing fields")
    try:
        db = conn()
        # hash password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        db.execute(
            "INSERT INTO users(username,email,password,role,is_active) VALUES(?,?,?,?,?)",
            (username, email, hashed, "user", 0)
        )
        db.commit()
        db.close()
        print("USER REGISTERED:", email)
        _registration_email_workflow(username, email)
        return jsonify(success=True)
    except sqlite3.IntegrityError:
        resent = _resend_activation_if_inactive(email, username_fallback=username)
        if resent:
            return jsonify(success=True, message="Activation email resent")
        return jsonify(success=False, error="Email already exists")
    except Exception as e:
        print(e)
        return jsonify(success=False, error=str(e))

# =========================
# API LOGIN
# =========================

@app.route("/login", methods=["POST"])
def login_form():
    email = request.form.get("email")
    password = request.form.get("password")
    next_url = sanitize_next_url(request.form.get("next"))
    db = conn()
    user = db.execute(
        "SELECT username,email,role,password,is_active,failed_login_count,locked_until FROM users WHERE email=?",
        (email,)
    ).fetchone()
    db.close()
    if user and _is_user_locked(user):
        return redirect(f"{STATIC_BASE_URL}/index.html?login=locked")
    if user and password and bcrypt.checkpw(password.encode(), user["password"].encode()):
        if (user["is_active"] or 0) == 0:
            return redirect(f"{STATIC_BASE_URL}/index.html?login=inactive")
        _reset_failed_login_state(user["email"])
        session["user"] = user["email"]
        # Append username to help static pages enable chat
        parsed = urlparse(next_url)
        query = dict(parse_qsl(parsed.query))
        query["user"] = user["username"]
        safe_next = urlunparse(parsed._replace(query=urlencode(query)))
        return redirect(safe_next)
    failed = _register_failed_login_attempt(user)
    if failed.get("locked"):
        return redirect(f"{STATIC_BASE_URL}/index.html?login=locked")
    return redirect(f"{STATIC_BASE_URL}/index.html?login=failed")

@app.route("/api/me", methods=["GET"])
def me():
    email = session.get("user")
    if not email:
        return jsonify(success=False), 401
    db = conn()
    user = db.execute(
        "SELECT username,email,role FROM users WHERE email=?",
        (email,)
    ).fetchone()
    db.close()
    if not user:
        return jsonify(success=False), 404
    return jsonify(success=True, user=dict(user))

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = conn()
    user = db.execute(
        "SELECT username,email,role,password,is_active,failed_login_count,locked_until FROM users WHERE email=?",
        (email,)
    ).fetchone()
    db.close()
    if user and _is_user_locked(user):
        return jsonify(success=False, error=_lock_message()), 423
    if user and password and bcrypt.checkpw(password.encode(), user["password"].encode()):
        if user["is_active"] == 0:
            return jsonify(success=False, error="Account not activated")
        _reset_failed_login_state(user["email"])
        print("LOGIN SUCCESS:", email)
        session["user"] = user["email"]
        user_payload = {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
        return jsonify(success=True, user=user_payload)
    failed = _register_failed_login_attempt(user)
    if failed.get("locked"):
        return jsonify(success=False, error=_lock_message()), 423
    return jsonify(success=False, error="Invalid login")


@app.route("/api/chat-login", methods=["POST"])
def chat_login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password")
    if not username or not password:
        return jsonify(success=False, error="Missing credentials"), 400

    db = conn()
    user = db.execute(
        "SELECT id,username,email,role,password,is_active,failed_login_count,locked_until FROM users WHERE username=? COLLATE NOCASE",
        (username,),
    ).fetchone()
    db.close()

    if user and _is_user_locked(user):
        return jsonify(success=False, error=_lock_message()), 423
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        if (user["is_active"] or 0) == 0:
            return jsonify(success=False, error="Account not activated"), 403
        _reset_failed_login_state(user["email"])
        session["chat_user"] = user["email"]
        _mark_chat_active(user["email"])
        user_payload = {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        }
        return jsonify(success=True, user=user_payload)
    failed = _register_failed_login_attempt(user)
    if failed.get("locked"):
        return jsonify(success=False, error=_lock_message()), 423
    return jsonify(success=False, error="Invalid credentials"), 401


@app.route("/api/chat/messages", methods=["GET"])
def chat_messages_get():
    email = session.get("chat_user") or session.get("user")
    if not email:
        return jsonify(success=False, error="Unauthorized"), 401

    try:
        since_id = int(request.args.get("since_id", "0"))
    except ValueError:
        since_id = 0

    db = conn()
    user = db.execute(
        "SELECT username,is_active FROM users WHERE email=?",
        (email,),
    ).fetchone()
    if not user or (user["is_active"] or 0) == 0:
        db.close()
        return jsonify(success=False, error="Unauthorized"), 401
    _mark_chat_active(email)

    rows = db.execute(
        """
        SELECT id, username, message, created_at
        FROM chat_messages
        WHERE id > ?
        ORDER BY id ASC
        LIMIT 100
        """,
        (since_id,),
    ).fetchall()
    db.close()

    payload = [
        {
            "id": r["id"],
            "username": r["username"],
            "message": r["message"],
            "timestamp": r["created_at"],
        }
        for r in rows
    ]
    return jsonify(success=True, messages=payload)


@app.route("/api/chat/messages", methods=["POST"])
def chat_messages_post():
    email = session.get("chat_user") or session.get("user")
    if not email:
        return jsonify(success=False, error="Unauthorized"), 401

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(success=False, error="Message required"), 400
    if len(message) > 500:
        return jsonify(success=False, error="Message too long"), 400

    db = conn()
    user = db.execute(
        "SELECT username,is_active FROM users WHERE email=?",
        (email,),
    ).fetchone()
    if not user or (user["is_active"] or 0) == 0:
        db.close()
        return jsonify(success=False, error="Unauthorized"), 401
    _mark_chat_active(email)

    db.execute(
        "INSERT INTO chat_messages(username,message) VALUES(?,?)",
        (user["username"], message),
    )
    db.commit()
    db.close()
    return jsonify(success=True)


@app.route("/api/chat/online", methods=["GET"])
def chat_online():
    return jsonify(success=True, online=_chat_online_count())


@app.route("/_debug/pdb", methods=["GET"])
def debug_pdb_breakpoint():
    if not ENABLE_PDB_ROUTE:
        return jsonify(success=False, error="PDB route disabled"), 404

    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify(success=False, error="Forbidden"), 403

    # For local debugging only: this pauses the Flask process in terminal.
    pdb.set_trace()
    return jsonify(success=True, message="Resumed after pdb breakpoint")

# =========================
# API CONTACT MESSAGE
# =========================

@app.route("/contact", methods=["POST"])
@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) if request.is_json else request.form
    data = data or {}
    session_email = (session.get("user") or "").strip().lower()
    if not session_email:
        return jsonify(success=False, error="Registration and approval required"), 401

    with conn() as db:
        user = db.execute(
            "SELECT username, email, is_active FROM users WHERE email=?",
            (session_email,),
        ).fetchone()
        subscriber = db.execute(
            """
            SELECT confirmed, unsubscribed
            FROM subscribers
            WHERE email=?
            """,
            (session_email,),
        ).fetchone()

    if not user:
        session.clear()
        return jsonify(success=False, error="Registration required"), 401
    if int(user["is_active"] or 0) == 0:
        return jsonify(success=False, error="Account approval required"), 403
    if not subscriber or int(subscriber["confirmed"] or 0) != 1 or int(subscriber["unsubscribed"] or 0) == 1:
        return jsonify(success=False, error="Newsletter confirmation required before contact access"), 403

    name = (user["username"] or data.get("name") or data.get("username") or "").strip()
    email = (user["email"] or "").strip().lower()
    message = (data.get("message") or "").strip()
    admin_email = (
        os.getenv("CONTACT_ADMIN_EMAIL")
        or os.getenv("BOXLETTER_EMAIL")
        or os.getenv("SMTP_FROM")
        or ""
    ).strip().lower()

    if not name or not email or not message:
        return jsonify(success=False, error="Missing fields")
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return jsonify(success=False, error="Invalid email"), 400

    try:
        with conn() as db:
            cur = db.execute(
                """
                INSERT INTO contact_messages(name,username,email,recipient_email,message,status,email_status,emailed_user,emailed_admin)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (name, name, email, admin_email, message, "new", "pending", 0, 0),
            )
            db.commit()
            message_id = cur.lastrowid

        emailed_admin = False
        emailed_user = False
        send_errors = []

        if admin_email:
            try:
                emailed_admin = send_email(
                    admin_email,
                    f"New message from {name}",
                    build_contact_admin_email(name, email, message),
                )
                if not emailed_admin:
                    send_errors.append("admin email failed")
            except Exception as e:
                send_errors.append(f"admin email exception: {e}")
        else:
            send_errors.append("admin email not configured")

        try:
            emailed_user = send_email(
                email,
                "Thanks, we got it",
                build_contact_user_ack_email(name),
            )
            if not emailed_user:
                send_errors.append("user confirmation email failed")
        except Exception as e:
            send_errors.append(f"user email exception: {e}")

        if emailed_admin and emailed_user:
            email_status = "sent"
        elif emailed_admin or emailed_user:
            email_status = "partial"
        else:
            email_status = "failed"

        with conn() as db2:
            db2.execute(
                """
                UPDATE contact_messages
                SET emailed_user=?,
                    emailed_admin=?,
                    email_status=?,
                    email_error=?,
                    emailed_at=CASE WHEN (? OR ?) THEN CURRENT_TIMESTAMP ELSE emailed_at END
                WHERE id=?
                """,
                (
                    1 if emailed_user else 0,
                    1 if emailed_admin else 0,
                    email_status,
                    "; ".join(send_errors) if send_errors else None,
                    1 if emailed_user else 0,
                    1 if emailed_admin else 0,
                    message_id,
                ),
            )
            db2.commit()

        print("MESSAGE STORED:", name)
        return jsonify(
            success=True,
            message_id=message_id,
            emailed_user=emailed_user,
            emailed_admin=emailed_admin,
            status="new",
            email_status=email_status,
        )
    except Exception as e:
        print(e)
        return jsonify(success=False, error=str(e))

# =========================
# API SHARED FILES
# =========================

@app.route("/api/shared-files", methods=["GET"])
def shared_files_list():
    try:
        limit = int(request.args.get("limit", "24"))
    except ValueError:
        limit = 24
    limit = max(1, min(limit, 100))

    with conn() as db:
        rows = db.execute(
            """
            SELECT id, file_name, image_data, uploader_email, created_at
            FROM shared_files
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    items = [
        {
            "id": r["id"],
            "file_name": r["file_name"],
            "image_data": r["image_data"],
            "uploader_email": r["uploader_email"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]
    return jsonify(success=True, items=items)


@app.route("/api/shared-files", methods=["POST"])
def shared_files_create():
    data = request.get_json(silent=True) or {}
    file_name = (data.get("file_name") or "poster.png").strip()[:120]
    image_data = (data.get("image_data") or "").strip()
    uploader_email = (session.get("user") or session.get("chat_user") or "").strip()

    if not image_data.startswith("data:image/"):
        return jsonify(success=False, error="Invalid image payload"), 400

    payload_size = len(image_data.encode("utf-8", errors="ignore"))
    if payload_size > SHARED_FILE_MAX_BYTES:
        return jsonify(success=False, error="Image too large"), 413

    with conn() as db:
        cur = db.execute(
            "INSERT INTO shared_files(file_name,image_data,uploader_email) VALUES(?,?,?)",
            (file_name, image_data, uploader_email),
        )
        db.commit()
        new_id = cur.lastrowid
        row = db.execute(
            "SELECT id,file_name,image_data,uploader_email,created_at FROM shared_files WHERE id=?",
            (new_id,),
        ).fetchone()

    return jsonify(
        success=True,
        item={
            "id": row["id"],
            "file_name": row["file_name"],
            "image_data": row["image_data"],
            "uploader_email": row["uploader_email"],
            "created_at": row["created_at"],
        },
    )

# =========================
# API SUBSCRIBE
# =========================

def _request_wants_json():
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.is_json


def _subscribe_payload():
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        return (
            (payload.get("username") or "").strip(),
            (payload.get("email") or "").strip().lower(),
            (payload.get("weighter") or "").strip(),
        )
    return (
        (request.form.get("username") or "").strip(),
        (request.form.get("email") or "").strip().lower(),
        (request.form.get("weighter") or "").strip(),
    )


def _subscribe_response(success=False, error=None, redirect_status="ok", status_code=200):
    if _request_wants_json():
        body = {"success": success}
        if error:
            body["error"] = error
        return jsonify(body), status_code
    return redirect(f"{STATIC_BASE_URL}/index.html?subscribe={redirect_status}")


def _newsletter_admin_allowed():
    if session.get("ok"):
        return True
    if NEWSLETTER_DEV_OPEN and _client_ip() in {"127.0.0.1", "::1"}:
        return True
    return False


def build_campaign_email_html(body, unsubscribe_token):
    safe_body = (body or "").replace("\n", "<br>")
    unsub_link = f"{PUBLIC_BASE_URL}/unsubscribe?token={unsubscribe_token}"
    return f"""
    <div style="font-family:Arial,sans-serif;">
      <div>{safe_body}</div>
      <hr style="margin:20px 0;border:none;border-top:1px solid #ddd;">
      <p style="font-size:12px;color:#777;">
        To unsubscribe from newsletter emails, click:
        <a href="{unsub_link}">Unsubscribe</a>
      </p>
    </div>
    """


@app.route("/subscribe", methods=["POST"])
@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    username, email, weighter = _subscribe_payload()

    if not username or not email:
        return _subscribe_response(error="Missing fields", redirect_status="failed", status_code=400)

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return _subscribe_response(error="Invalid email", redirect_status="failed", status_code=400)

    try:
        token = uuid.uuid4().hex
        unsubscribe_token = uuid.uuid4().hex
        with conn() as db:
            db.execute(
                """
                INSERT INTO subscribers(username,email,weighter,confirmed,confirm_token,unsubscribed,unsubscribe_token)
                VALUES(?,?,?,?,?,?,?)
                """,
                (username, email, weighter, 0, token, 0, unsubscribe_token),
            )

        print("SUBSCRIBER ADDED (unconfirmed):", email)

        user_email_sent = send_email(
            email,
            "Confirm your newsletter subscription",
            build_subscriber_confirm_email(username, token),
        )

        boxletter = os.getenv("BOXLETTER_EMAIL")
        admin_email_sent = False
        if boxletter:
            admin_email_sent = send_email(
                boxletter,
                "New newsletter subscriber",
                build_boxletter_notice(username, email, weighter),
            )

        if _request_wants_json():
            return jsonify(
                success=True,
                message="Subscription pending confirmation",
                user_email_sent=user_email_sent,
                admin_email_sent=admin_email_sent,
            )

        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=pending")

    except sqlite3.IntegrityError:
        try:
            with conn() as db:
                existing = db.execute(
                    "SELECT confirmed, username FROM subscribers WHERE email=?",
                    (email,),
                ).fetchone()
                if existing and existing["confirmed"] == 0:
                    token = uuid.uuid4().hex
                    db.execute(
                        """
                        UPDATE subscribers
                        SET username=?, weighter=?, confirm_token=?, unsubscribed=0,
                            unsubscribe_token=COALESCE(NULLIF(unsubscribe_token,''),?)
                        WHERE email=?
                        """,
                        (username, weighter, token, uuid.uuid4().hex, email),
                    )
                    send_email(
                        email,
                        "Confirm your newsletter subscription",
                        build_subscriber_confirm_email(username, token),
                    )
                    if _request_wants_json():
                        return jsonify(success=True, message="Confirmation email resent")
                    return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=pending")
        except Exception as e:
            print("SUBSCRIBE DUPLICATE RECOVERY ERROR:", e)
        return _subscribe_response(error="Email already subscribed", redirect_status="exists", status_code=409)
    except Exception as e:
        print("SUBSCRIBE ERROR:", e)
        return _subscribe_response(error="Subscription failed", redirect_status="failed", status_code=500)


@app.route("/confirm", methods=["GET"])
def confirm_subscriber():
    token = (request.args.get("token") or "").strip()
    if not token:
        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=invalid")

    try:
        with conn() as db:
            row = db.execute(
                "SELECT id, username, email, confirmed FROM subscribers WHERE confirm_token=?",
                (token,),
            ).fetchone()
            if not row:
                return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=invalid")

            if row["confirmed"] == 0:
                db.execute(
                    "UPDATE subscribers SET confirmed=1, confirm_token=NULL WHERE id=?",
                    (row["id"],),
                )
                send_email(
                    row["email"],
                    "Newsletter subscription confirmed",
                    build_newsletter_email(row["username"]),
                )
                return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=confirmed")

        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=already")
    except Exception as e:
        print("CONFIRM SUBSCRIBER ERROR:", e)
        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=failed")


@app.route("/unsubscribe", methods=["GET"])
def unsubscribe_newsletter():
    token = (request.args.get("token") or "").strip()
    if not token:
        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=invalid")
    try:
        with conn() as db:
            row = db.execute(
                "SELECT id FROM subscribers WHERE unsubscribe_token=?",
                (token,),
            ).fetchone()
            if not row:
                return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=invalid")
            db.execute("UPDATE subscribers SET unsubscribed=1 WHERE id=?", (row["id"],))
            db.commit()
        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=unsubscribed")
    except Exception as e:
        print("UNSUBSCRIBE ERROR:", e)
        return redirect(f"{STATIC_BASE_URL}/index.html?subscribe=failed")


@app.route("/api/campaigns", methods=["POST"])
def campaigns_create():
    if not _newsletter_admin_allowed():
        return jsonify(success=False, error="Forbidden"), 403

    data = request.get_json(silent=True) or {}
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()
    if not subject or not body:
        return jsonify(success=False, error="Subject and body required"), 400

    with conn() as db:
        cur = db.execute(
            "INSERT INTO campaigns(subject, body, status) VALUES(?,?,?)",
            (subject, body, "draft"),
        )
        db.commit()
        campaign_id = cur.lastrowid

    return jsonify(success=True, campaign_id=campaign_id)


@app.route("/api/newsletter/sync-users", methods=["POST"])
def newsletter_sync_users():
    if not _newsletter_admin_allowed():
        return jsonify(success=False, error="Forbidden"), 403

    stats = _sync_users_to_subscribers()
    return jsonify(success=True, **stats)


@app.route("/api/campaigns/<int:campaign_id>/send", methods=["POST"])
def campaigns_send(campaign_id):
    if not _newsletter_admin_allowed():
        return jsonify(success=False, error="Forbidden"), 403

    data = request.get_json(silent=True) or {}
    try:
        batch_size = int(data.get("batch_size", 25))
    except (TypeError, ValueError):
        batch_size = 25
    batch_size = max(1, min(batch_size, 200))

    with conn() as db:
        campaign = db.execute(
            "SELECT id,subject,body FROM campaigns WHERE id=?",
            (campaign_id,),
        ).fetchone()
        if not campaign:
            return jsonify(success=False, error="Campaign not found"), 404

        recipients = db.execute(
            """
            SELECT s.id, s.email, s.unsubscribe_token
            FROM subscribers s
            LEFT JOIN campaign_sends cs
              ON cs.campaign_id=? AND cs.subscriber_id=s.id
            WHERE s.confirmed=1
              AND COALESCE(s.unsubscribed,0)=0
              AND cs.id IS NULL
            ORDER BY s.id ASC
            LIMIT ?
            """,
            (campaign_id, batch_size),
        ).fetchall()

    sent_count = 0
    failed_count = 0
    for r in recipients:
        unsubscribe_token = (r["unsubscribe_token"] or uuid.uuid4().hex).strip()
        if not r["unsubscribe_token"]:
            with conn() as db_fix:
                db_fix.execute(
                    "UPDATE subscribers SET unsubscribe_token=? WHERE id=?",
                    (unsubscribe_token, r["id"]),
                )
                db_fix.commit()

        ok = send_email(
            r["email"],
            campaign["subject"],
            build_campaign_email_html(campaign["body"], unsubscribe_token),
        )
        with conn() as db_log:
            if ok:
                sent_count += 1
                db_log.execute(
                    """
                    INSERT OR REPLACE INTO campaign_sends(campaign_id,subscriber_id,status,error,sent_at)
                    VALUES(?,?,?,?,CURRENT_TIMESTAMP)
                    """,
                    (campaign_id, r["id"], "sent", None),
                )
            else:
                failed_count += 1
                db_log.execute(
                    """
                    INSERT OR REPLACE INTO campaign_sends(campaign_id,subscriber_id,status,error,sent_at)
                    VALUES(?,?,?,?,CURRENT_TIMESTAMP)
                    """,
                    (campaign_id, r["id"], "failed", "send_email returned False"),
                )
            db_log.commit()

    with conn() as db:
        remaining = db.execute(
            """
            SELECT COUNT(*)
            FROM subscribers s
            LEFT JOIN campaign_sends cs
              ON cs.campaign_id=? AND cs.subscriber_id=s.id
            WHERE s.confirmed=1
              AND COALESCE(s.unsubscribed,0)=0
              AND cs.id IS NULL
            """,
            (campaign_id,),
        ).fetchone()[0]

        status = "sending" if remaining > 0 else "completed"
        db.execute("UPDATE campaigns SET status=? WHERE id=?", (status, campaign_id))
        db.commit()

    return jsonify(
        success=True,
        campaign_id=campaign_id,
        batch_size=batch_size,
        processed=len(recipients),
        sent=sent_count,
        failed=failed_count,
        remaining=remaining,
        status=status,
    )


@app.route("/api/campaigns/<int:campaign_id>/sends", methods=["GET"])
def campaigns_sends_list(campaign_id):
    if not _newsletter_admin_allowed():
        return jsonify(success=False, error="Forbidden"), 403

    with conn() as db:
        rows = db.execute(
            """
            SELECT cs.subscriber_id, s.email, cs.status, cs.error, cs.sent_at
            FROM campaign_sends cs
            JOIN subscribers s ON s.id = cs.subscriber_id
            WHERE cs.campaign_id=?
            ORDER BY cs.id ASC
            """,
            (campaign_id,),
        ).fetchall()
    items = [dict(r) for r in rows]
    return jsonify(success=True, campaign_id=campaign_id, items=items)


@app.route("/admin/newsletter", methods=["POST"])
def admin_newsletter_send():
    if not _newsletter_admin_allowed():
        return jsonify(success=False, error="Forbidden"), 403

    payload = request.get_json(silent=True) if request.is_json else request.form
    payload = payload or {}
    subject = (payload.get("subject") or "").strip()
    body = (payload.get("body") or "").strip()
    if not subject or not body:
        if request.is_json:
            return jsonify(success=False, error="Subject and body required"), 400
        return "<p>Subject and body required.</p>", 400

    sent_count = 0
    failed_count = 0
    with conn() as db:
        cur = db.execute(
            "INSERT INTO campaigns(subject, body, status) VALUES(?,?,?)",
            (subject, body, "sending"),
        )
        campaign_id = cur.lastrowid
        recipients = db.execute(
            """
            SELECT id, email, unsubscribe_token
            FROM subscribers
            WHERE confirmed=1
              AND COALESCE(unsubscribed,0)=0
            ORDER BY id ASC
            """
        ).fetchall()

        for r in recipients:
            unsubscribe_token = (r["unsubscribe_token"] or uuid.uuid4().hex).strip()
            if not r["unsubscribe_token"]:
                db.execute(
                    "UPDATE subscribers SET unsubscribe_token=? WHERE id=?",
                    (unsubscribe_token, r["id"]),
                )
            ok = send_email(
                r["email"],
                subject,
                build_campaign_email_html(body, unsubscribe_token),
            )
            db.execute(
                """
                INSERT OR REPLACE INTO campaign_sends(campaign_id,subscriber_id,status,error,sent_at)
                VALUES(?,?,?,?,CURRENT_TIMESTAMP)
                """,
                (
                    campaign_id,
                    r["id"],
                    "sent" if ok else "failed",
                    None if ok else "send_email returned False",
                ),
            )
            if ok:
                sent_count += 1
            else:
                failed_count += 1

        db.execute(
            "UPDATE campaigns SET status=? WHERE id=?",
            ("completed" if failed_count == 0 else "partial", campaign_id),
        )
        db.commit()

    if request.is_json:
        return jsonify(
            success=True,
            campaign_id=campaign_id,
            sent=sent_count,
            failed=failed_count,
        )
    return (
        f"<p>Newsletter sent. campaign_id={campaign_id}, sent={sent_count}, failed={failed_count}</p>"
        "<p><a href='/dashboard'>Back</a></p>"
    )


# =========================
# API USER EMAIL SYSTEM
# =========================

@app.route("/api/user/email/send", methods=["POST"])
def user_email_send():
    user_email = (session.get("user") or "").strip().lower()
    if not user_email:
        return jsonify(success=False, error="Unauthorized"), 401

    data = request.get_json(silent=True) or {}
    to_email = (data.get("to_email") or "").strip().lower()
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()

    if not to_email or not subject or not body:
        return jsonify(success=False, error="Missing fields"), 400
    if "@" not in to_email or "." not in to_email.rsplit("@", 1)[-1]:
        return jsonify(success=False, error="Invalid recipient email"), 400

    rec = UserEmailMessageModel(
        user_email=user_email,
        to_email=to_email,
        subject=subject,
        body=body,
        status="pending",
    )
    db_orm.session.add(rec)
    db_orm.session.commit()
    msg_id = rec.id

    email_html = f"""
    <div style="font-family:Arial,sans-serif;">
      <p>{html_escape(body).replace(chr(10), "<br>")}</p>
    </div>
    """
    ok = send_email(to_email, subject, email_html)
    rec = db_orm.session.get(UserEmailMessageModel, msg_id)
    if rec:
        if ok:
            rec.status = "sent"
            rec.error = None
            db_orm.session.execute(
                db_orm.text("UPDATE user_email_messages SET sent_at=CURRENT_TIMESTAMP WHERE id=:id"),
                {"id": msg_id},
            )
        else:
            rec.status = "failed"
            rec.error = "send_email returned False"
        db_orm.session.commit()

    return jsonify(success=True, id=msg_id, status=("sent" if ok else "failed"))


@app.route("/api/user/email/history", methods=["GET"])
def user_email_history():
    user_email = (session.get("user") or "").strip().lower()
    if not user_email:
        return jsonify(success=False, error="Unauthorized"), 401

    try:
        limit = int(request.args.get("limit", "50"))
    except ValueError:
        limit = 50
    limit = max(1, min(limit, 200))

    rows = (
        UserEmailMessageModel.query
        .filter_by(user_email=user_email)
        .order_by(UserEmailMessageModel.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": r.id,
            "to_email": r.to_email,
            "subject": r.subject,
            "status": r.status,
            "error": r.error,
            "created_at": str(r.created_at) if r.created_at else None,
            "sent_at": str(r.sent_at) if r.sent_at else None,
        }
        for r in rows
    ]
    return jsonify(success=True, items=items)


# =========================
# ORDERS / PAYMENTS API
# =========================

@app.route("/api/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    customer_name = (data.get("customer_name") or "").strip()
    customer_email = (data.get("customer_email") or "").strip().lower()
    currency = (data.get("currency") or "USD").strip().upper() or "USD"
    source = (data.get("source") or "web").strip().lower() or "web"
    notes = (data.get("notes") or "").strip()

    if not isinstance(items, list) or not items:
        return jsonify(success=False, error="Missing order items"), 400

    clean_items = []
    amount_total = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        product_name = (item.get("name") or item.get("product_name") or "").strip()
        if not product_name:
            continue
        quantity = max(1, int(item.get("qty") or item.get("quantity") or 1))
        unit_price = _as_money(item.get("price") or item.get("unit_price") or 0)
        line_total = _as_money(unit_price * quantity)
        amount_total += line_total
        clean_items.append({
            "product_id": (item.get("id") or item.get("product_id") or "").strip(),
            "product_name": product_name,
            "unit_price": unit_price,
            "quantity": quantity,
            "line_total": line_total,
        })

    if not clean_items:
        return jsonify(success=False, error="No valid order items"), 400

    order_code = _safe_order_code()
    with conn() as db:
        cur = db.execute(
            """
            INSERT INTO orders(order_code, customer_name, customer_email, currency, amount_total, status, source, notes)
            VALUES (?, ?, ?, ?, ?, 'pending_payment', ?, ?)
            """,
            (order_code, customer_name, customer_email, currency, amount_total, source, notes),
        )
        order_id = cur.lastrowid
        for item in clean_items:
            db.execute(
                """
                INSERT INTO order_items(order_id, product_id, product_name, unit_price, quantity, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["product_name"],
                    item["unit_price"],
                    item["quantity"],
                    item["line_total"],
                ),
            )
        db.commit()

    payload = _read_order_with_items(order_id)
    return jsonify(success=True, order=payload["order"], items=payload["items"])


@app.route("/api/orders/<order_code>", methods=["GET"])
def get_order(order_code):
    payload = _read_order_by_code((order_code or "").strip())
    if not payload:
        return jsonify(success=False, error="Order not found"), 404
    return jsonify(success=True, order=payload["order"], items=payload["items"])


@app.route("/api/orders/recent", methods=["GET"])
def recent_orders():
    limit = request.args.get("limit", "10")
    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 10
    return jsonify(success=True, orders=_recent_orders(limit_value))


@app.route("/api/orders/customers", methods=["GET"])
def customer_orders():
    limit = request.args.get("limit", "10")
    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 10
    return jsonify(success=True, customers=_customer_purchase_history(limit_value))


@app.route("/api/payouts", methods=["GET"])
def list_payout_requests():
    limit = request.args.get("limit", "10")
    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 10
    return jsonify(success=True, payouts=_recent_payout_requests(limit_value))


@app.route("/api/payouts/config", methods=["GET"])
def payout_config():
    return jsonify(
        success=True,
        stripe_ready=_stripe_payouts_ready(),
        payments_enabled=PAYMENTS_ENABLED,
    )


@app.route("/api/payouts/request", methods=["POST"])
def request_payout():
    data = request.get_json(silent=True) or {}
    destination_label = (data.get("destination_label") or "").strip()
    notes = (data.get("notes") or "").strip()
    provider = (data.get("provider") or "manual_bank").strip() or "manual_bank"
    currency = (data.get("currency") or "USD").strip().upper() or "USD"
    account_holder = (data.get("account_holder") or "").strip()
    bank_name = (data.get("bank_name") or "").strip()
    account_number = (data.get("account_number") or "").strip()
    iban = (data.get("iban") or "").strip()

    try:
        amount = _as_money(data.get("amount") or 0)
    except Exception:
        amount = 0

    if not destination_label:
        return jsonify(success=False, error="Destination label required"), 400
    if amount <= 0:
        return jsonify(success=False, error="Amount must be greater than zero"), 400

    with conn() as db:
        cur = db.execute(
            """
            INSERT INTO payout_requests(
                destination_label, amount, currency, provider, status, notes,
                account_holder, bank_name, account_number, iban
            )
            VALUES (?, ?, ?, ?, 'requested', ?, ?, ?, ?, ?)
            """,
            (
                destination_label,
                amount,
                currency,
                provider,
                notes,
                account_holder or None,
                bank_name or None,
                account_number or None,
                iban or None,
            ),
        )
        db.commit()
        payout_id = cur.lastrowid
        row = db.execute("SELECT * FROM payout_requests WHERE id=?", (payout_id,)).fetchone()

    _append_audit_log("cash_till", "payout_requested", f"{provider}:{amount:.2f}:{destination_label}")
    return jsonify(success=True, payout=dict(row))


@app.route("/api/payouts/<int:payout_id>/execute", methods=["POST"])
def execute_payout(payout_id):
    with conn() as db:
        row = db.execute("SELECT * FROM payout_requests WHERE id=?", (payout_id,)).fetchone()
    if not row:
        return jsonify(success=False, error="Payout request not found"), 404

    payout = dict(row)
    provider = str(payout.get("provider") or "").strip().lower()
    status = str(payout.get("status") or "").strip().lower()

    if provider != "stripe":
        return jsonify(success=False, error="Only Stripe payout execution is supported right now"), 400
    if status not in ("requested", "failed"):
        return jsonify(success=False, error="Payout is not executable in its current state"), 409
    if not _stripe_payouts_ready():
        return jsonify(success=False, error="Stripe payouts are not configured"), 400

    try:
        stripe_payout = _create_stripe_payout(payout)
    except urllib_error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        with conn() as db:
            db.execute(
                """
                UPDATE payout_requests
                SET status='failed', failure_reason=?, provider_response_json=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (error_body[:500], error_body[:2000], payout_id),
            )
            db.commit()
        return jsonify(success=False, error="Stripe payout creation failed", details=error_body[:500]), 502
    except Exception as e:
        with conn() as db:
            db.execute(
                """
                UPDATE payout_requests
                SET status='failed', failure_reason=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (str(e)[:500], payout_id),
            )
            db.commit()
        return jsonify(success=False, error=f"Stripe payout creation failed: {e}"), 502

    provider_payout_id = str(stripe_payout.get("id") or "").strip()
    payout_status = str(stripe_payout.get("status") or "pending").strip().lower() or "pending"
    with conn() as db:
        db.execute(
            """
            UPDATE payout_requests
            SET provider='stripe',
                provider_payout_id=?,
                provider_response_json=?,
                failure_reason=NULL,
                status=?,
                executed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (provider_payout_id or None, json.dumps(stripe_payout), payout_status, payout_id),
        )
        db.commit()
        updated = db.execute("SELECT * FROM payout_requests WHERE id=?", (payout_id,)).fetchone()
    _append_audit_log("cash_till", "payout_executed", f"stripe:{payout_id}:{provider_payout_id}:{payout_status}")
    return jsonify(success=True, payout=dict(updated), stripe=stripe_payout)


@app.route("/api/payments/<provider>/create", methods=["POST"])
def create_payment_session(provider):
    provider = (provider or "").strip().lower()
    if provider not in ("paypal", "card", "bitcoin"):
        return jsonify(success=False, error="Unsupported provider"), 400

    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    if not order_code:
        return jsonify(success=False, error="Missing order code"), 400

    payload = _read_order_by_code(order_code)
    if not payload:
        return jsonify(success=False, error="Order not found"), 404

    order = payload["order"]
    checkout_url = _provider_checkout_url(provider, order_code)
    provider_ready = _payment_provider_ready(provider)
    provider_payment_id = f"{provider.upper()}-{uuid.uuid4().hex[:14].upper()}"
    metadata = {
        "payments_enabled": PAYMENTS_ENABLED,
        "provider_ready": provider_ready,
        "mode": ("live_stub" if provider_ready and PAYMENTS_ENABLED else "mock"),
        "order_code": order_code,
    }
    payment_status = ("created" if provider_ready and PAYMENTS_ENABLED else "mock_pending")

    if provider == "card" and provider_ready and PAYMENTS_ENABLED:
        try:
            stripe_session = _create_stripe_checkout_session(order, payload["items"])
            checkout_url = stripe_session.get("url") or checkout_url
            provider_payment_id = stripe_session.get("id") or provider_payment_id
            metadata = {
                **metadata,
                "mode": "stripe_checkout",
                "stripe_status": stripe_session.get("status"),
                "stripe_payment_status": stripe_session.get("payment_status"),
            }
            payment_status = "checkout_created"
        except urllib_error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            return jsonify(success=False, error="Stripe session creation failed", details=error_body[:500]), 502
        except Exception as e:
            return jsonify(success=False, error=f"Stripe session creation failed: {e}"), 502
    elif provider == "paypal" and provider_ready and PAYMENTS_ENABLED:
        try:
            paypal_order = _create_paypal_checkout_order(order, payload["items"])
            provider_payment_id = str(paypal_order.get("id") or provider_payment_id)
            metadata = {
                **metadata,
                "mode": "paypal_sdk",
                "paypal_status": paypal_order.get("status"),
            }
            payment_status = "checkout_created"
        except urllib_error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            return jsonify(success=False, error="PayPal order creation failed", details=error_body[:500]), 502
        except Exception as e:
            return jsonify(success=False, error=f"PayPal order creation failed: {e}"), 502
    elif provider == "bitcoin" and provider_ready and PAYMENTS_ENABLED:
        try:
            btcpay_invoice = _create_btcpay_invoice(order, payload["items"])
            provider_payment_id = str(btcpay_invoice.get("id") or provider_payment_id)
            checkout_url = (
                btcpay_invoice.get("checkoutLink")
                or btcpay_invoice.get("url")
                or checkout_url
            )
            metadata = {
                **metadata,
                "mode": "btcpay_invoice",
                "btcpay_status": btcpay_invoice.get("status"),
            }
            payment_status = "checkout_created"
        except urllib_error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            return jsonify(success=False, error="BTCPay invoice creation failed", details=error_body[:500]), 502
        except Exception as e:
            return jsonify(success=False, error=f"BTCPay invoice creation failed: {e}"), 502

    with conn() as db:
        cur = db.execute(
            """
            INSERT INTO payments(order_id, provider, provider_payment_id, provider_checkout_url, amount, currency, status, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["id"],
                provider,
                provider_payment_id,
                checkout_url,
                order["amount_total"],
                order["currency"],
                payment_status,
                json.dumps(metadata),
            ),
        )
        payment_id = cur.lastrowid
        db.execute(
            "UPDATE orders SET status='payment_created', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (order["id"],),
        )
        db.commit()
    _append_audit_log("system", "payment_session_created", f"{provider}:{order_code}:{provider_payment_id}:{payment_status}")

    return jsonify(
        success=True,
        provider=provider,
        mode=metadata["mode"],
        provider_ready=provider_ready,
        payment={
            "id": payment_id,
            "provider_payment_id": provider_payment_id,
            "checkout_url": checkout_url,
            "status": payment_status,
        },
        order=order,
        warning=(
            None
            if provider_ready and PAYMENTS_ENABLED
            else "Provider credentials not configured or live payments disabled. Using mock checkout session."
        ),
    )


@app.route("/api/payments/confirm", methods=["POST"])
def confirm_mock_payment():
    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    provider = (data.get("provider") or "").strip().lower()
    _append_audit_log("browser", "payment_confirm_blocked", f"{provider}:{order_code}")
    return (
        jsonify(
            success=False,
            error="Payment finalization is webhook-only. Browser confirmation is disabled.",
        ),
        403,
    )


@app.route("/api/payments/submit", methods=["POST"])
def submit_payment_details():
    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    provider = (data.get("provider") or "").strip().lower()
    provider_payment_id = (data.get("provider_payment_id") or "").strip()
    details = data.get("details") or {}

    if not order_code or not provider:
      return jsonify(success=False, error="Missing order code or provider"), 400
    if not isinstance(details, dict):
      return jsonify(success=False, error="Invalid payment details"), 400

    ok, error_message, payment = _record_payment_submission(
        order_code,
        provider,
        provider_payment_id,
        details,
    )
    if not ok:
        return jsonify(success=False, error=error_message), 404 if error_message in ("Order not found", "Payment record not found") else 400
    _append_audit_log("browser", "payment_submitted", f"{provider}:{order_code}:{payment.get('provider_payment_id') or provider_payment_id}")
    return jsonify(success=True, payment=payment)


@app.route("/api/payments/recent", methods=["GET"])
def recent_payments():
    limit = request.args.get("limit", "25")
    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 25
    return jsonify(success=True, payments=_recent_payments(limit_value))


@app.route("/api/payments/paypal/config", methods=["GET"])
def paypal_checkout_config():
    ready = _payment_provider_ready("paypal") and PAYMENTS_ENABLED
    return jsonify(
        success=True,
        ready=ready,
        client_id=PAYPAL_CLIENT_ID if ready else "",
        env=PAYPAL_ENV,
        currency="USD",
    )


@app.route("/api/payments/card/config", methods=["GET"])
def card_checkout_config():
    ready = _payment_provider_ready("card") and PAYMENTS_ENABLED
    return jsonify(
        success=True,
        ready=ready,
        provider="stripe",
        payments_enabled=PAYMENTS_ENABLED,
        webhook_configured=bool(STRIPE_WEBHOOK_SECRET),
    )


@app.route("/api/checkout/send-code", methods=["POST"])
def checkout_send_code():
    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    delivery_method = (data.get("delivery_method") or "").strip().lower()
    target = (data.get("target") or "").strip()
    if not order_code:
        return jsonify(success=False, error="Missing order code"), 400
    payload = _read_order_by_code(order_code)
    if not payload:
        return jsonify(success=False, error="Order not found"), 404
    if delivery_method != "email":
        return jsonify(success=False, error="Only email verification is connected right now."), 400
    if not _is_valid_email(target):
        return jsonify(success=False, error="Invalid email address"), 400

    _cleanup_checkout_verifications()
    verification_code = f"{secrets.randbelow(900000) + 100000}"
    client_ip = _client_ip()
    key = _checkout_verification_key(order_code, client_ip)
    CHECKOUT_VERIFICATIONS[key] = {
        "code": verification_code,
        "target": target,
        "delivery_method": delivery_method,
        "verified": False,
        "order_code": order_code,
        "expires_at": int(time.time()) + CHECKOUT_CODE_TTL_SECONDS,
    }
    email_sent = send_email(
        target,
        f"CYBERGHOST verification code for {order_code}",
        (
            f"<p>Your CYBERGHOST checkout verification code is <strong>{verification_code}</strong>.</p>"
            f"<p>Order: <strong>{html_escape(order_code)}</strong></p>"
            f"<p>This code expires in {CHECKOUT_CODE_TTL_SECONDS // 60} minutes.</p>"
        ),
    )
    _append_audit_log("checkout", "verification_code_sent", f"{order_code}:{delivery_method}:{target}:{'sent' if email_sent else 'failed'}")
    if not email_sent:
        CHECKOUT_VERIFICATIONS.pop(key, None)
        return jsonify(success=False, error=_email_provider_failure_message(), provider=_resolve_email_provider()), 502
    return jsonify(success=True, message=f"Verification code sent to {target}.")


@app.route("/api/checkout/verify-code", methods=["POST"])
def checkout_verify_code():
    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    delivery_method = (data.get("delivery_method") or "").strip().lower()
    target = (data.get("target") or "").strip()
    code = (data.get("code") or "").strip()
    if not order_code or not code:
        return jsonify(success=False, error="Missing order code or verification code"), 400

    _cleanup_checkout_verifications()
    client_ip = _client_ip()
    key = _checkout_verification_key(order_code, client_ip)
    item = CHECKOUT_VERIFICATIONS.get(key)
    if not item:
        return jsonify(success=False, error="No active verification code found. Send a new code first."), 404
    if item.get("delivery_method") != delivery_method or item.get("target") != target:
        return jsonify(success=False, error="Verification target mismatch. Send a new code and retry."), 400
    if item.get("code") != code:
        return jsonify(success=False, error="Verification code mismatch."), 400

    item["verified"] = True
    item["verified_at"] = int(time.time())
    item["expires_at"] = int(time.time()) + CHECKOUT_VERIFIED_TTL_SECONDS
    CHECKOUT_VERIFICATIONS[key] = item
    _append_audit_log("checkout", "verification_code_accepted", f"{order_code}:{delivery_method}:{target}")
    return jsonify(success=True, message="Verification passed.")


@app.route("/api/payments/paypal/capture", methods=["POST"])
def paypal_capture_payment():
    if not (_payment_provider_ready("paypal") and PAYMENTS_ENABLED):
        return jsonify(success=False, error="PayPal is not configured"), 400

    data = request.get_json(silent=True) or {}
    order_code = (data.get("order_code") or "").strip()
    paypal_order_id = (data.get("provider_payment_id") or "").strip()
    if not order_code or not paypal_order_id:
        return jsonify(success=False, error="Missing order code or PayPal order id"), 400
    _cleanup_checkout_verifications()
    verification = CHECKOUT_VERIFICATIONS.get(_checkout_verification_key(order_code, _client_ip()))
    if not verification or not verification.get("verified"):
        return jsonify(success=False, error="Checkout verification required before PayPal capture."), 403

    payload = _read_order_by_code(order_code)
    if not payload:
        return jsonify(success=False, error="Order not found"), 404

    with conn() as db:
        payment_row = db.execute(
            """
            SELECT *
            FROM payments
            WHERE order_id=? AND provider='paypal' AND provider_payment_id=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (payload["order"]["id"], paypal_order_id),
        ).fetchone()
    if not payment_row:
        return jsonify(success=False, error="Payment session not found"), 404
    if str(payment_row["status"] or "").strip().lower() == "paid":
        return jsonify(success=True, already_paid=True, order=payload["order"])

    try:
        capture = _capture_paypal_order(paypal_order_id)
    except urllib_error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        return jsonify(success=False, error="PayPal capture failed", details=error_body[:500]), 502
    except Exception as e:
        return jsonify(success=False, error=f"PayPal capture failed: {e}"), 502

    capture_status = str(capture.get("status") or "").strip().upper()
    if capture_status != "COMPLETED":
        return jsonify(success=False, error="PayPal capture not completed", details=capture), 409

    ok, error_message, payload = _finalize_paypal_payment(
        order_code,
        paypal_order_id,
        metadata={
            "mode": "paypal_sdk",
            "paypal_capture_status": capture_status,
            "paypal_capture_id": (
                (((capture.get("purchase_units") or [{}])[0].get("payments") or {}).get("captures") or [{}])[0].get("id")
            ),
            "paypal_response": capture,
        },
    )
    if not ok:
        return jsonify(success=False, error=error_message or "Unable to finalize PayPal payment"), 409
    _append_audit_log("paypal", "payment_finalized", f"paypal:{order_code}:{paypal_order_id}")
    return jsonify(success=True, order_code=order_code, provider_payment_id=paypal_order_id, details=capture)


def _log_webhook_event(provider):
    data = request.get_json(silent=True)
    raw_payload = request.get_data(cache=True, as_text=True)
    event_type = ""
    event_id = ""
    if isinstance(data, dict):
        event_type = str(data.get("type") or data.get("event_type") or "").strip()
        event_id = str(data.get("id") or data.get("event_id") or "").strip()
    signature = (
        request.headers.get("Stripe-Signature")
        or request.headers.get("Paypal-Transmission-Sig")
        or request.headers.get("BTCPay-Sig")
        or ""
    )
    with conn() as db:
        db.execute(
            """
            INSERT INTO webhook_events(provider, event_type, event_id, signature, payload_json, processed)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (provider, event_type, event_id, signature, raw_payload[:250000], 0),
        )
        db.commit()
    _append_audit_log("webhook", "webhook_received", f"{provider}:{event_type}:{event_id}")


@app.route("/api/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    raw_payload = request.get_data(cache=True, as_text=True)
    signature = request.headers.get("Stripe-Signature", "")
    if STRIPE_WEBHOOK_SECRET:
        if not _verify_stripe_signature(raw_payload, signature, STRIPE_WEBHOOK_SECRET):
            return jsonify(success=False, error="Invalid Stripe signature"), 400

    _log_webhook_event("stripe")
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("type") or "").strip()
    obj = ((data.get("data") or {}).get("object") or {}) if isinstance(data, dict) else {}

    if event_type == "checkout.session.completed" and isinstance(obj, dict):
        order_code = (
            str(obj.get("client_reference_id") or "").strip()
            or str((obj.get("metadata") or {}).get("order_code") or "").strip()
        )
        stripe_session_id = str(obj.get("id") or "").strip()
        if order_code:
            payload = _read_order_by_code(order_code)
            if payload:
                with conn() as db:
                    db.execute(
                        """
                        UPDATE payments
                        SET status='paid', updated_at=CURRENT_TIMESTAMP
                        WHERE order_id=? AND provider='card' AND provider_payment_id=?
                        """,
                        (payload["order"]["id"], stripe_session_id),
                    )
                    db.execute(
                        "UPDATE orders SET status='paid', updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (payload["order"]["id"],),
                    )
                    db.execute(
                        """
                        UPDATE webhook_events
                        SET processed=1
                        WHERE provider='stripe' AND event_id=?
                        """,
                        (str(data.get("id") or "").strip(),),
                    )
                    db.commit()
                _append_audit_log("stripe", "payment_finalized", f"card:{order_code}:{stripe_session_id}")
    elif event_type in ("payout.created", "payout.updated", "payout.paid", "payout.failed") and isinstance(obj, dict):
        stripe_payout_id = str(obj.get("id") or "").strip()
        payout_status = str(obj.get("status") or "").strip().lower()
        failure_reason = str(obj.get("failure_message") or obj.get("failure_code") or "").strip()
        if stripe_payout_id:
            with conn() as db:
                db.execute(
                    """
                    UPDATE payout_requests
                    SET status=?,
                        failure_reason=?,
                        provider_response_json=?,
                        updated_at=CURRENT_TIMESTAMP
                    WHERE provider='stripe' AND provider_payout_id=?
                    """,
                    (payout_status or "pending", failure_reason or None, json.dumps(obj), stripe_payout_id),
                )
                db.execute(
                    """
                    UPDATE webhook_events
                    SET processed=1
                    WHERE provider='stripe' AND event_id=?
                    """,
                    (str(data.get("id") or "").strip(),),
                )
                db.commit()
            _append_audit_log("stripe", "payout_updated", f"{event_type}:{stripe_payout_id}:{payout_status}")
    return jsonify(success=True)


@app.route("/api/webhooks/paypal", methods=["POST"])
def paypal_webhook():
    raw_payload = request.get_data(cache=True, as_text=True)
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("event_type") or data.get("type") or "").strip()
    event_id = str(data.get("id") or data.get("event_id") or "").strip()

    if not (_payment_provider_ready("paypal") and PAYMENTS_ENABLED):
        return jsonify(success=False, error="PayPal is not configured"), 400
    if not PAYPAL_WEBHOOK_ID:
        return jsonify(success=False, error="PAYPAL_WEBHOOK_ID is not configured"), 400

    try:
        verification = _verify_paypal_webhook_signature(raw_payload, request.headers, data)
    except urllib_error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        return jsonify(success=False, error="PayPal webhook verification failed", details=error_body[:500]), 502
    except Exception as e:
        return jsonify(success=False, error=f"PayPal webhook verification failed: {e}"), 502

    if str((verification or {}).get("verification_status") or "").strip().upper() != "SUCCESS":
        return jsonify(success=False, error="Invalid PayPal webhook signature", details=verification), 400

    _log_webhook_event("paypal")

    resource = data.get("resource") or {}
    related_ids = ((resource.get("supplementary_data") or {}).get("related_ids") or {}) if isinstance(resource, dict) else {}
    paypal_order_id = (
        str(related_ids.get("order_id") or "").strip()
        or str(resource.get("id") or "").strip()
    )

    if event_type == "PAYMENT.CAPTURE.COMPLETED" and paypal_order_id:
        payload, payment_row = _find_order_by_paypal_order_id(paypal_order_id)
        if payload and payment_row:
            ok, _, _ = _finalize_paypal_payment(
                payload["order"]["order_code"],
                paypal_order_id,
                metadata={
                    "mode": "paypal_webhook",
                    "paypal_webhook_event_id": event_id,
                    "paypal_webhook_event_type": event_type,
                    "paypal_capture_id": str(resource.get("id") or "").strip(),
                    "paypal_response": data,
                },
            )
            if ok:
                _append_audit_log("paypal", "payment_finalized_webhook", f"paypal:{payload['order']['order_code']}:{paypal_order_id}")

    _mark_webhook_event_processed("paypal", event_id)
    return jsonify(success=True, event_type=event_type, event_id=event_id)


@app.route("/api/webhooks/btcpay", methods=["POST"])
def btcpay_webhook():
    raw_payload = request.get_data(cache=True, as_text=True)
    signature = (
        request.headers.get("BTCPay-Sig")
        or request.headers.get("Btcpay-Sig")
        or request.headers.get("btcpay-sig")
        or ""
    )
    if BTCPAY_WEBHOOK_SECRET and not _verify_btcpay_signature(raw_payload, signature, BTCPAY_WEBHOOK_SECRET):
        return jsonify(success=False, error="Invalid BTCPay signature"), 400

    _log_webhook_event("btcpay")
    data = request.get_json(silent=True) or {}
    event_type = str(data.get("type") or data.get("event_type") or "").strip()
    event_id = str(data.get("id") or data.get("event_id") or "").strip()
    invoice_id = (
        str(data.get("invoiceId") or "").strip()
        or str(((data.get("data") or {}) if isinstance(data.get("data"), dict) else {}).get("id") or "").strip()
    )
    order_code = (
        str(data.get("orderId") or "").strip()
        or str(((data.get("metadata") or {}) if isinstance(data.get("metadata"), dict) else {}).get("orderCode") or "").strip()
    )

    if invoice_id and not order_code:
        payload, _ = _find_order_by_btcpay_invoice_id(invoice_id)
        if payload:
            order_code = str(payload["order"]["order_code"] or "").strip()

    should_finalize = False
    invoice_details = {}
    if invoice_id and _payment_provider_ready("bitcoin") and PAYMENTS_ENABLED:
        try:
            invoice_details = _get_btcpay_invoice(invoice_id)
        except Exception:
            invoice_details = {}
        invoice_status = str(invoice_details.get("status") or "").strip().lower()
        should_finalize = invoice_status in {"settled", "complete", "paid"}
    else:
        should_finalize = event_type.lower() in {
            "invoice_settled",
            "invoicesettled",
            "invoiceconfirmed",
        }

    if should_finalize and order_code and invoice_id:
        ok, _, payload = _finalize_btcpay_payment(
            order_code,
            invoice_id,
            metadata={
                "mode": "btcpay_webhook",
                "btcpay_webhook_event_id": event_id,
                "btcpay_webhook_event_type": event_type,
                "btcpay_invoice": invoice_details or data,
            },
        )
        if ok:
            with conn() as db:
                db.execute(
                    """
                    UPDATE webhook_events
                    SET processed=1
                    WHERE provider='btcpay' AND event_id=?
                    """,
                    (event_id,),
                )
                db.commit()
            _append_audit_log("btcpay", "payment_finalized", f"bitcoin:{order_code}:{invoice_id}")

    return jsonify(success=True, event_type=event_type, event_id=event_id, invoice_id=invoice_id)

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    chat_email = session.get("chat_user")
    if chat_email:
        ACTIVE_CHAT_USERS.pop(chat_email, None)
    session.clear()
    return redirect("/")

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CYBERGHOST Flask webapp")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 8011)))
    args = parser.parse_args()

    # Hard gate: on port 8011 only the configured Windows user can run this app.
    if args.port == 8011 and os.name == "nt":
        current_user = _current_windows_user()
        if current_user != PORT_8081_ALLOWED_WINDOWS_USER:
            print(
                f"Access denied for port 8011. "
                f"Allowed user: {PORT_8081_ALLOWED_WINDOWS_USER}, current user: {current_user}"
            )
            raise SystemExit(1)

    validate_email_runtime_config()
    run_local_server(args.host, args.port)
