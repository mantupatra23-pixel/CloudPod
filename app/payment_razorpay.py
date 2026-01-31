import razorpay
import os

client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET")
    )
)

def create_order(amount_rupees: int):
    order = client.order.create({
        "amount": amount_rupees * 100,  # paise
        "currency": "INR",
        "payment_capture": 1
    })
    return order
