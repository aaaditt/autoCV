"""
/api/payments — Payment handling for AutoCV.
Supports manual payments (PayPal / bank transfer) with admin verification.
Stripe integration available as optional upgrade path.
"""
import os
import uuid
from flask import Blueprint, request, jsonify, session, current_app

payments_bp = Blueprint("payments", __name__)

# Optional Stripe support (only if keys are configured)
try:
    import stripe
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    PRICE_SINGLE = os.environ.get("STRIPE_PRICE_SINGLE")
    PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO")
    STRIPE_ENABLED = bool(stripe.api_key and PRICE_SINGLE)
except ImportError:
    STRIPE_ENABLED = False


@payments_bp.route("/payments/status", methods=["GET"])
def payment_status():
    """Check if current user has an active payment/plan."""
    user = session.get("user")
    if not user:
        return jsonify({"plan": "free", "authenticated": False})

    plan = session.get("plan", "free")
    return jsonify({
        "plan": plan,
        "authenticated": True,
        "payment_method": "manual"
    })


@payments_bp.route("/payments/request", methods=["POST"])
def payment_request():
    """
    Log a manual payment request.
    Frontend sends plan type after user sends PayPal/bank payment.
    Admin manually verifies and upgrades via Supabase dashboard.
    """
    data = request.get_json() or {}
    plan = data.get("plan", "single")
    email = data.get("email", session.get("user", {}).get("email", "unknown"))

    current_app.logger.info(f"Manual payment request: plan={plan}, email={email}")

    return jsonify({
        "status": "pending",
        "message": "Payment request received. Your account will be upgraded within 24 hours after payment verification.",
        "plan": plan,
        "paypal_email": "aaditchandra2212@gmail.com",
        "contact_email": "work.aadit@gmail.com"
    })


# ── Stripe Routes (only active if Stripe keys are configured) ──

@payments_bp.route("/payments/checkout/single", methods=["POST"])
def checkout_single():
    """Create a one-time checkout session (Stripe or manual fallback)."""
    if not STRIPE_ENABLED:
        return jsonify({
            "error": "Online checkout is not available. Please use PayPal or bank transfer.",
            "paypal_email": "aaditchandra2212@gmail.com"
        }), 400

    try:
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        optimization_id = str(uuid.uuid4())
        session["pending_optimization_id"] = optimization_id

        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": PRICE_SINGLE, "quantity": 1}],
            mode="payment",
            success_url=f"{frontend_url}/pages/payment-success.html?session_id={{CHECKOUT_SESSION_ID}}&oid={optimization_id}",
            cancel_url=f"{frontend_url}/pages/optimize.html?cancelled=true",
            metadata={"optimization_id": optimization_id, "type": "single"}
        )
        return jsonify({"checkout_url": checkout.url, "session_id": checkout.id})
    except Exception as e:
        current_app.logger.error(f"Checkout error: {e}")
        return jsonify({"error": "Could not create checkout session"}), 500


@payments_bp.route("/payments/checkout/pro", methods=["POST"])
def checkout_pro():
    """Create a subscription checkout session (Stripe or manual fallback)."""
    if not STRIPE_ENABLED:
        return jsonify({
            "error": "Online checkout is not available. Please use PayPal or bank transfer.",
            "paypal_email": "aaditchandra2212@gmail.com"
        }), 400

    try:
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": PRICE_PRO, "quantity": 1}],
            mode="subscription",
            success_url=f"{frontend_url}/pages/payment-success.html?session_id={{CHECKOUT_SESSION_ID}}&type=pro",
            cancel_url=f"{frontend_url}/pages/pricing.html?cancelled=true",
            metadata={"type": "pro"}
        )
        return jsonify({"checkout_url": checkout.url})
    except Exception as e:
        current_app.logger.error(f"Pro checkout error: {e}")
        return jsonify({"error": "Could not create checkout session"}), 500


@payments_bp.route("/payments/webhook", methods=["POST"])
def webhook():
    """Stripe webhook handler (only if Stripe is configured)."""
    if not STRIPE_ENABLED:
        return jsonify({"error": "Stripe not configured"}), 400

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception:
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        current_app.logger.info(f"Payment confirmed: {sess.get('metadata', {})}")

    return jsonify({"received": True})
