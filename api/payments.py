import os
import json
import hmac
import hashlib
import time
import requests
import base64
from flask import Blueprint, request, jsonify

payments_bp = Blueprint('payments', __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "").strip()
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "sandbox").strip().lower()

def _stripe_headers():
    token = base64.b64encode(f"{STRIPE_SECRET_KEY}:".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}

def _stripe_checkout_success_url(order_code, base_url):
    return f"{base_url}/cash_till.html?stripe=success&order={order_code}"

def _stripe_checkout_cancel_url(order_code, base_url):
    return f"{base_url}/cash_till.html?stripe=cancel&order={order_code}"

@payments_bp.route("/api/payments/<provider>/create", methods=["POST"])
def create_payment(provider):
    data = request.get_json()
    amount = data.get("amount", 0)
    currency = data.get("currency", "eur")
    items = data.get("items", [])
    base_url = data.get("base_url", os.getenv("STATIC_BASE_URL", "http://127.0.0.1:8011"))
    
    if provider == "stripe":
        if not STRIPE_SECRET_KEY:
            return jsonify(success=False, error="Stripe not configured"), 400
        
        order_code = f"ORD-{int(time.time())}"
        
        line_items = []
        for item in items:
            line_items.append({
                "price_data": {
                    "currency": currency,
                    "product_data": {
                        "name": item.get("name", "Product")
                    },
                    "unit_amount": int(item.get("amount", amount) * 100)
                },
                "quantity": item.get("quantity", 1)
            })
        
        if not line_items:
            line_items = [{
                "price_data": {
                    "currency": currency,
                    "product_data": {"name": "Payment"},
                    "unit_amount": int(amount * 100)
                },
                "quantity": 1
            }]
        
        session_data = {
            "mode": "payment",
            "line_items": line_items,
            "success_url": _stripe_checkout_success_url(order_code, base_url),
            "cancel_url": _stripe_checkout_cancel_url(order_code, base_url)
        }
        
        try:
            response = requests.post(
                "https://api.stripe.com/v1/checkout/sessions",
                data=session_data,
                headers=_stripe_headers()
            )
            result = response.json()
            
            if result.get("id"):
                return jsonify(success=True, session_id=result["id"], url=result["url"])
            return jsonify(success=False, error=result.get("error", "Unknown error")), 400
        except Exception as e:
            return jsonify(success=False, error=str(e)), 500
    
    return jsonify(success=False, error=f"Provider {provider} not supported"), 400

@payments_bp.route("/api/payments/card/config", methods=["GET"])
def card_config():
    return jsonify(success=True, enabled=bool(STRIPE_SECRET_KEY))

@payments_bp.route("/api/webhooks/stripe", methods=["POST"])
def stripe_webhook():
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify(success=False, error="Webhook not configured"), 400
    
    payload = request.data
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        import stripe
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return jsonify(success=False, error="Invalid signature"), 400
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_code = session.get("metadata", {}).get("order_code")
    
    return jsonify(success=True)

def init_payments(app):
    app.register_blueprint(payments_bp)
