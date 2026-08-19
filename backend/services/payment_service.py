import random
import time


class PaymentGatewaySandbox:
    """Simulated payment gateway sandbox for UPI, Card, and Cash on Delivery."""

    @staticmethod
    def process_upi_payment(upi_id: str, amount: float):
        if not upi_id or "@" not in upi_id:
            return {"success": False, "message": "Invalid UPI VPA ID format. Example: name@upi"}
        
        txn_ref = f"UPI-{int(time.time())}-{random.randint(1000, 9999)}"
        return {
            "success": True,
            "transaction_ref": txn_ref,
            "message": f"UPI Payment of ₹{amount:,.2f} verified successfully."
        }

    @staticmethod
    def process_card_payment(card_number: str, expiry: str, cvv: str, amount: float):
        clean_card = card_number.replace(" ", "").replace("-", "")
        if len(clean_card) < 13 or not clean_card.isdigit():
            return {"success": False, "message": "Invalid Card Number."}
        if len(cvv) < 3 or not cvv.isdigit():
            return {"success": False, "message": "Invalid CVV code."}

        txn_ref = f"CARD-{int(time.time())}-{random.randint(1000, 9999)}"
        return {
            "success": True,
            "transaction_ref": txn_ref,
            "message": f"Card Payment of ₹{amount:,.2f} processed successfully."
        }

    @staticmethod
    def process_cod_payment(amount: float):
        txn_ref = f"COD-{int(time.time())}-{random.randint(1000, 9999)}"
        return {
            "success": True,
            "transaction_ref": txn_ref,
            "message": f"Cash on Delivery order confirmed for ₹{amount:,.2f}."
        }
