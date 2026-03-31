import os
import hmac
import hashlib
import time
import requests
import base64
import json

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

def get_stripe_headers():
    token = base64.b64encode(f"{STRIPE_SECRET_KEY}:".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}

def create_checkout_session(amount, currency, items, success_url, cancel_url, metadata=None):
    if not STRIPE_SECRET_KEY:
        return None, "Stripe not configured"
    
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
        "success_url": success_url,
        "cancel_url": cancel_url
    }
    
    if metadata:
        session_data["metadata"] = metadata
        session_data["metadata"]["order_code"] = order_code
    
    try:
        response = requests.post(
            "https://api.stripe.com/v1/checkout/sessions",
            data=session_data,
            headers=get_stripe_headers()
        )
        result = response.json()
        
        if result.get("id"):
            return {"session_id": result["id"], "url": result["url"], "order_code": order_code}, None
        return None, result.get("error", "Unknown error")
    except Exception as e:
        return None, str(e)

def verify_webhook(payload, signature):
    if not STRIPE_WEBHOOK_SECRET:
        return None, "Webhook not configured"
    
    try:
        expected_sig = hmac.new(
            STRIPE_WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, signature):
            return None, "Invalid signature"
        
        return json.loads(payload), None
    except Exception as e:
        return None, str(e)

def is_stripe_configured():
    return bool(STRIPE_SECRET_KEY)
