"""GLANCE Stripe Checkout integration — hosted checkout sessions."""

import os
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")

PRODUCTS = {
    "analyse_instantanee": {
        "name": "GLANCE \u2014 Analyse Instantan\u00e9e",
        "description": "Analyse IA compl\u00e8te de votre Graphical Abstract : arch\u00e9type, score, recommandations",
        "price_cents": 2900,  # 29.00 EUR
        "currency": "eur",
    },
    "audit_complet": {
        "name": "GLANCE \u2014 Audit Complet",
        "description": "Analyse IA + test avec 10 lecteurs r\u00e9els + rapport Spin/Drift/Warp",
        "price_cents": 9900,  # 99.00 EUR
        "currency": "eur",
    },
}


def is_stripe_configured() -> bool:
    """Return True if Stripe secret key is set."""
    return bool(stripe.api_key)


def create_checkout_session(
    product_key: str,
    ga_id: int,
    success_url: str,
    cancel_url: str,
    customer_email: str = None,
) -> str:
    """Create a Stripe Checkout Session and return the URL."""
    product = PRODUCTS[product_key]

    params = {
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price_data": {
                    "currency": product["currency"],
                    "product_data": {
                        "name": product["name"],
                        "description": product["description"],
                    },
                    "unit_amount": product["price_cents"],
                },
                "quantity": 1,
            }
        ],
        "mode": "payment",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {
            "ga_id": str(ga_id),
            "product": product_key,
        },
    }

    if customer_email:
        params["customer_email"] = customer_email

    session = stripe.checkout.Session.create(**params)
    return session.url


def verify_session(session_id: str) -> dict:
    """Verify a checkout session is paid."""
    session = stripe.checkout.Session.retrieve(session_id)
    return {
        "paid": session.payment_status == "paid",
        "email": session.customer_details.email if session.customer_details else None,
        "ga_id": session.metadata.get("ga_id"),
        "product": session.metadata.get("product"),
    }
