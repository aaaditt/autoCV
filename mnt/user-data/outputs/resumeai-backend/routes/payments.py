"""
/api/payments — Stripe checkout and webhook handling.
Creates checkout sessions and processes payment confirmations.
"""
import os
import uuid
import stripe
from flask import Blueprint, request, jsonify, session, current_app

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

PRICE_SINGLE = os.environ.get("STRIPE_PRICE_SINGLE")   # $19
PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO")          # $29/mo

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/checkout/single", methods=["POST"])
def checkout_single():
    """Create a $19 one-time checkout session."""
    try:
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        optimization_id = str(uuid.uuid4())

        # Store optimization ID in session
        session["pending_optimization_id"] = optimization_id

        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_SINGLE,
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}&oid={optimization_id}",
            cancel_url=f"{frontend_url}/optimize?cancelled=true",
            metadata={
                "optimization_id": optimization_id,
                "type": "single"
            }
        )

        return jsonify({
            "checkout_url": checkout.url,
            "session_id": checkout.id
        })

    except Exception as e:
        current_app.logger.error(f"Checkout error: {e}")
        return jsonify({"error": "Could not create checkout session"}), 500


@payments_bp.route("/checkout/pro", methods=["POST"])
def checkout_pro():
    """Create a $29/month subscription checkout session."""
    try:
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_PRO,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}&type=pro",
            cancel_url=f"{frontend_url}/pricing?cancelled=true",
            metadata={"type": "pro"}
        )

        return jsonify({"checkout_url": checkout.url})

    except Exception as e:
        current_app.logger.error(f"Pro checkout error: {e}")
        return jsonify({"error": "Could not create checkout session"}), 500


@payments_bp.route("/webhook", methods=["POST"])
def webhook():
    """
    Stripe webhook handler.
    Verifies payment and unlocks optimization.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        current_app.logger.error("Webhook signature verification failed")
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        sess = event["data"]["object"]
        _handle_payment_success(sess)

    elif event["type"] == "customer.subscription.deleted":
        # Handle subscription cancellation
        sub = event["data"]["object"]
        current_app.logger.info(f"Subscription cancelled: {sub['id']}")

    return jsonify({"received": True})


@payments_bp.route("/verify/<session_id>", methods=["GET"])
def verify_payment(session_id):
    """
    Frontend calls this after redirect from Stripe.
    Verifies payment and sets session flag.
    """
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        if checkout_session.payment_status == "paid":
            optimization_id = checkout_session.metadata.get("optimization_id")

            # Set payment verified in session
            session["payment_verified"] = True
            session["optimization_id"] = optimization_id

            return jsonify({
                "paid": True,
                "optimization_id": optimization_id,
                "type": checkout_session.metadata.get("type", "single")
            })
        else:
            return jsonify({"paid": False}), 402

    except Exception as e:
        current_app.logger.error(f"Verify error: {e}")
        return jsonify({"error": "Could not verify payment"}), 500


def _handle_payment_success(checkout_session):
    """Internal: handle successful payment from webhook."""
    optimization_id = checkout_session.get("metadata", {}).get("optimization_id")
    payment_type = checkout_session.get("metadata", {}).get("type")
    current_app.logger.info(
        f"Payment confirmed: {optimization_id} type={payment_type}"
    )
