from flask import current_app


def discounted_price(price, discount_percent):
    return round(float(price) * (1 - float(discount_percent or 0) / 100), 2)


def apply_coupon(subtotal, coupon):
    if not coupon:
        return 0.0

    if subtotal < float(coupon["min_order_amount"] or 0):
        return 0.0

    if coupon["discount_type"] == "percent":
        discount = subtotal * (float(coupon["discount_value"]) / 100)
    else:
        discount = float(coupon["discount_value"])

    max_discount = float(coupon.get("max_discount") or discount)
    return round(min(discount, max_discount), 2)


def delivery_fee(total_after_discount):
    cfg = current_app.config
    if total_after_discount >= float(cfg["FREE_DELIVERY_MIN_TOTAL"]):
        return 0.0
    return float(cfg["DEFAULT_DELIVERY_FEE"])
