import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout(amount_usd: int):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "CloudPod Wallet Topup"},
                "unit_amount": amount_usd * 100
            },
            "quantity": 1
        }],
        mode="payment",
        success_url="https://cloudpod.app/success",
        cancel_url="https://cloudpod.app/cancel"
    )
    return session
