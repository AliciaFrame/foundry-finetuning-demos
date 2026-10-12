"""Zava Post-Purchase Resolution Desk - tool implementations for hosted agent."""
import json
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "zava_db.json")
TODAY = datetime(2026, 7, 15)

_db_cache = None


def _load_db():
    global _db_cache
    if _db_cache is None:
        with open(DB_PATH) as f:
            _db_cache = json.load(f)
    return _db_cache


RETURN_WINDOWS = {
    "standard": {"apparel": 30, "home": 30, "electronics": 15, "personal_care": 15},
    "gold":     {"apparel": 45, "home": 45, "electronics": 30, "personal_care": 30},
    "platinum": {"apparel": 60, "home": 60, "electronics": 45, "personal_care": 45},
}


def _get_return_window(tier, category):
    tier_w = RETURN_WINDOWS.get(tier, RETURN_WINDOWS["standard"])
    return tier_w.get(category, 30)


def _is_defective(reason):
    r = reason.lower()
    return any(w in r for w in [
        "defective", "broken", "damaged", "faulty", "malfunction",
        "defect", "cracked", "flicker", "doesn't work", "not working",
        "damaged_in_shipping",
    ])


# ---------------------------------------------------------------------------
# Tool 1: get_order_details
# ---------------------------------------------------------------------------
def get_order_details(order_id: str) -> str:
    db = _load_db()
    order = db["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    customer = db["customers"].get(order["customer_id"])
    if not customer:
        return json.dumps({"error": f"Customer not found for order {order_id}"})

    enriched_items = []
    for li in order["line_items"]:
        product = db["products"].get(li["product_id"])
        on_sale = product.get("on_sale", False) if product else False
        enriched_items.append({
            "item_id": li["item_id"],
            "product_id": li["product_id"],
            "product_name": li.get("name", product["name"] if product else "Unknown"),
            "category": li.get("category", product["category"] if product else "unknown"),
            "sku": li["sku"],
            "quantity": li["qty"],
            "unit_price": li["unit_price"],
            "discount_pct": li["discount_pct"],
            "on_sale": on_sale,
            "variant": li.get("variant", ""),
        })

    return json.dumps({
        "order_id": order.get("order_id", order_id),
        "customer": {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "loyalty_tier": customer["loyalty_tier"],
        },
        "order_date": order["order_date"],
        "promised_delivery": order.get("promised_delivery"),
        "items": enriched_items,
        "subtotal": order["subtotal"],
        "tax": order["tax"],
        "total": order["total"],
        "payment_method": order["payment_method"],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: get_fulfillment_status
# ---------------------------------------------------------------------------
def get_fulfillment_status(order_id: str) -> str:
    db = _load_db()
    order = db["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    fulfillment = order.get("fulfillment", {})
    items = []
    for item_id, ful in fulfillment.items():
        delivery_date = ful.get("delivery_date")
        days_since = None
        if delivery_date:
            days_since = (TODAY - datetime.fromisoformat(delivery_date)).days

        days_late = None
        promised = ful.get("promised_delivery_date")
        if ful.get("late_delivery") and delivery_date and promised:
            days_late = (datetime.fromisoformat(delivery_date) - datetime.fromisoformat(promised)).days

        items.append({
            "item_id": item_id,
            "status": ful["status"],
            "ship_date": ful.get("ship_date"),
            "delivery_date": delivery_date,
            "carrier": ful.get("carrier"),
            "late_delivery": ful.get("late_delivery", False),
            "days_late": days_late,
            "days_since_delivery": days_since,
        })

    return json.dumps({
        "order_id": order_id,
        "today": "2026-07-15",
        "items": items,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: check_resolution_policy
# ---------------------------------------------------------------------------
def check_resolution_policy(order_id: str, item_id: str, reason: str) -> str:
    db = _load_db()
    order = db["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    li = next((i for i in order["line_items"] if i["item_id"] == item_id), None)
    if not li:
        return json.dumps({"error": f"Item {item_id} not found in order {order_id}"})

    product = db["products"].get(li["product_id"])
    customer = db["customers"].get(order["customer_id"])
    tier = customer["loyalty_tier"] if customer else "standard"

    ful = order.get("fulfillment", {}).get(item_id, {})

    status = ful.get("status", "unknown")
    category = li.get("category", product.get("category", "home") if product else "home")
    on_sale = product.get("on_sale", False) if product else False
    is_late = ful.get("late_delivery", False)
    is_defect = _is_defective(reason)
    is_lost = status == "lost"
    is_processing = status in ("processing", "pending")

    delivery_str = ful.get("delivery_date")
    days_since = None
    if delivery_str:
        days_since = (TODAY - datetime.fromisoformat(delivery_str)).days

    base_window = _get_return_window(tier, category)
    effective_window = base_window + (15 if is_late else 0)

    shipping_credit = 10.0 if is_late else 0.0

    if is_defect or is_lost or is_processing:
        restocking_pct = 0.0
    elif category == "electronics":
        restocking_pct = {"platinum": 0.0, "gold": 7.5}.get(tier, 15.0)
    else:
        restocking_pct = 0.0

    eligible = True
    eligible_actions = ["refund", "exchange", "replacement", "store_credit"]
    denial_reason = None
    special_rules = []

    if is_lost:
        eligible_actions = ["refund", "replacement"]
        special_rules.append("Lost package: full refund or replacement, no restocking fee")
    elif is_processing:
        eligible_actions = ["cancel"]
        special_rules.append("Order still processing: eligible for cancellation with full refund")
    elif on_sale and not is_defect:
        eligible = False
        eligible_actions = []
        denial_reason = "Final sale item: no returns or exchanges"
        special_rules.append("Sale/clearance items are final sale")
    elif on_sale and is_defect:
        eligible_actions = ["store_credit"]
        special_rules.append("Defective sale item: store credit only")
    elif category == "personal_care" and not is_defect:
        eligible = False
        eligible_actions = []
        denial_reason = "Personal care items cannot be returned once opened"
        special_rules.append("Personal care: non-returnable unless defective")
    elif is_defect:
        special_rules.append("Defective item: eligible regardless of window or category")
    elif days_since is not None and days_since > effective_window:
        eligible = False
        eligible_actions = []
        denial_reason = (
            f"Return window expired: {days_since} days since delivery, "
            f"window is {effective_window} days"
        )

    if is_late:
        special_rules.append("Late delivery: $10 shipping credit applies")

    return json.dumps({
        "order_id": order_id,
        "item_id": item_id,
        "eligible": eligible,
        "eligible_actions": eligible_actions,
        "category": category,
        "loyalty_tier": tier,
        "return_window_days": effective_window,
        "days_since_delivery": days_since,
        "restocking_fee_pct": restocking_pct,
        "shipping_credit": shipping_credit,
        "on_sale": on_sale,
        "is_defective": is_defect,
        "special_rules": special_rules,
        "denial_reason": denial_reason,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: check_inventory
# ---------------------------------------------------------------------------
def check_inventory(sku: str) -> str:
    db = _load_db()
    inv = db.get("inventory", {}).get(sku)
    if not inv:
        product = db["products"].get(sku)
        if product and product.get("variants"):
            alternatives = []
            for v in product["variants"]:
                v_inv = db["inventory"].get(v["sku"], {})
                if v_inv.get("in_stock"):
                    alternatives.append({
                        "sku": v["sku"],
                        "variant": v["variant"],
                        "quantity": v_inv["quantity"],
                    })
            return json.dumps({
                "sku": sku,
                "in_stock": False,
                "quantity": 0,
                "note": "Base product SKU — check specific variants",
                "available_variants": alternatives,
            }, indent=2)
        return json.dumps({"sku": sku, "in_stock": False, "quantity": 0,
                           "note": "SKU not found in inventory"}, indent=2)

    result = {"sku": sku, "in_stock": inv["in_stock"], "quantity": inv["quantity"]}
    if not inv["in_stock"]:
        result["restock_date"] = inv.get("restock_date")

    base_id = sku.rsplit("-", 1)[0] if "-" in sku else sku
    product = db["products"].get(base_id)
    if product and product.get("variants"):
        alternatives = []
        for v in product["variants"]:
            if v["sku"] != sku:
                v_inv = db["inventory"].get(v["sku"], {})
                if v_inv.get("in_stock"):
                    alternatives.append({
                        "sku": v["sku"],
                        "variant": v["variant"],
                        "quantity": v_inv["quantity"],
                    })
        if alternatives:
            result["alternative_variants_in_stock"] = alternatives

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: calculate_resolution
# ---------------------------------------------------------------------------
def calculate_resolution(order_id: str, items: list | str) -> str:
    db = _load_db()
    order = db["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid items format - expected JSON array"})

    customer = db["customers"].get(order["customer_id"])
    tier = customer["loyalty_tier"] if customer else "standard"
    fulfillment = order.get("fulfillment", {})

    breakdown = []
    total_refund = 0.0
    total_restocking = 0.0
    total_shipping_credit = 0.0
    warnings = []

    for ai in items:
        item_id = ai.get("item_id")
        action = ai.get("action")
        reason = ai.get("reason", "")

        if action == "shipping_credit":
            ful = fulfillment.get(item_id, {})
            if ful.get("late_delivery"):
                total_shipping_credit += 10.0
                breakdown.append({
                    "item_id": item_id, "action": "shipping_credit",
                    "amount": 10.0, "reason": "Late delivery compensation",
                })
            else:
                warnings.append(f"Shipping credit for {item_id}: delivery was not late")
            continue

        if action == "deny":
            breakdown.append({
                "item_id": item_id, "action": "deny",
                "refund_amount": 0.0, "restocking_fee": 0.0, "net_refund": 0.0,
                "reason": reason,
            })
            continue

        li = next((i for i in order["line_items"] if i["item_id"] == item_id), None)
        if not li:
            warnings.append(f"Item {item_id} not found in order")
            continue

        product = db["products"].get(li["product_id"])
        category = li.get("category", product.get("category", "home") if product else "home")
        unit_price = li["unit_price"]
        qty = li["qty"]
        item_total = round(unit_price * qty, 2)
        if li.get("discount_pct", 0) > 0:
            item_total = round(item_total * (1 - li["discount_pct"] / 100), 2)

        ful = fulfillment.get(item_id, {})
        is_defect = _is_defective(reason)
        is_lost = ful.get("status") == "lost"
        is_processing = ful.get("status") in ("processing", "pending")

        if action in ("refund", "store_credit"):
            if is_defect or is_lost or is_processing:
                rpct = 0.0
            elif category == "electronics":
                rpct = {"platinum": 0.0, "gold": 7.5}.get(tier, 15.0)
            else:
                rpct = 0.0

            rfee = round(item_total * rpct / 100, 2)
            net = round(item_total - rfee, 2)
            breakdown.append({
                "item_id": item_id, "action": action,
                "refund_amount": item_total, "restocking_fee": rfee,
                "restocking_fee_pct": rpct, "net_refund": net,
            })
            total_refund += net
            total_restocking += rfee

        elif action == "replacement":
            breakdown.append({
                "item_id": item_id, "action": "replacement",
                "refund_amount": item_total, "restocking_fee": 0.0,
                "net_refund": item_total,
                "note": "Replacement item shipped at no cost",
            })
            total_refund += item_total

        elif action == "exchange":
            exchange_sku = ai.get("exchange_sku", li["sku"])
            exchange_product = db["products"].get(exchange_sku)
            if not exchange_product:
                prefix = exchange_sku.rsplit("-", 1)[0] if "-" in exchange_sku else exchange_sku
                exchange_product = db["products"].get(prefix)
            exchange_price = exchange_product["price"] if exchange_product else unit_price
            price_diff = round(exchange_price - unit_price, 2)

            entry = {
                "item_id": item_id, "action": "exchange",
                "original_price": unit_price, "exchange_sku": exchange_sku,
                "exchange_price": exchange_price, "price_difference": price_diff,
                "restocking_fee": 0.0,
            }
            if price_diff > 0:
                entry["customer_owes"] = price_diff
                entry["net_refund"] = 0.0
            elif price_diff < 0:
                entry["customer_credit"] = abs(price_diff)
                entry["net_refund"] = abs(price_diff)
                total_refund += abs(price_diff)
            else:
                entry["net_refund"] = 0.0
            breakdown.append(entry)

    total_resolution = round(total_refund + total_shipping_credit, 2)

    result = {
        "order_id": order_id,
        "breakdown": breakdown,
        "summary": {
            "total_refund": round(total_refund, 2),
            "total_restocking_fees": round(total_restocking, 2),
            "total_shipping_credit": round(total_shipping_credit, 2),
            "total_resolution_amount": total_resolution,
        },
        "refund_method": order["payment_method"],
    }
    if warnings:
        result["warnings"] = warnings
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 6: submit_resolution
# ---------------------------------------------------------------------------
def submit_resolution(order_id: str, resolution_summary: str) -> str:
    db = _load_db()
    order = db["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    customer = db["customers"].get(order["customer_id"])
    cust_name = customer["name"] if customer else "Customer"
    cust_email = customer["email"] if customer else ""

    conf_hash = hashlib.md5(
        f"{order_id}-{resolution_summary}".encode()
    ).hexdigest()[:8].upper()
    confirmation_id = f"RES-{conf_hash}"

    return json.dumps({
        "confirmation_id": confirmation_id,
        "order_id": order_id,
        "status": "submitted",
        "summary": resolution_summary,
        "customer_notification": {
            "to": cust_email,
            "name": cust_name,
            "subject": f"Zava Resolution Confirmation - {confirmation_id}",
        },
        "estimated_processing": "5-7 business days",
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool schemas - Responses API format (flat, no nested "function" key)
# ---------------------------------------------------------------------------
TOOL_SCHEMAS_RESPONSES = [
    {
        "type": "function",
        "name": "get_order_details",
        "description": (
            "Retrieve order details: line items (item_id, product_name, category, "
            "sku, quantity, unit_price, discount_pct, on_sale), customer info (name, "
            "email, loyalty_tier), payment method, dates, subtotal, tax, total. "
            "Always call this first."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, e.g. 'ORD-001'",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "type": "function",
        "name": "get_fulfillment_status",
        "description": (
            "Get per-item shipping/fulfillment status. Returns each item's status "
            "(processing/shipped/delivered/lost), ship_date, delivery_date, carrier, "
            "late_delivery flag, days_late, and days_since_delivery."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "type": "function",
        "name": "check_resolution_policy",
        "description": (
            "Check resolution eligibility for ONE item. Returns: eligible (bool), "
            "eligible_actions, return_window_days, days_since_delivery, "
            "restocking_fee_pct, shipping_credit, special_rules, denial_reason. "
            "Call once PER item needing resolution."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID"},
                "item_id": {
                    "type": "string",
                    "description": "The line item ID, e.g. 'LI-002'",
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Customer's reason: 'defective', 'buyers_remorse', "
                        "'wrong_item', 'doesnt_fit', 'changed_mind', "
                        "'damaged_in_shipping', or 'opened_not_needed'."
                    ),
                },
            },
            "required": ["order_id", "item_id", "reason"],
        },
    },
    {
        "type": "function",
        "name": "check_inventory",
        "description": (
            "Check stock for a SKU. Returns in_stock, quantity, restock_date "
            "(if OOS), and alternative in-stock variants. "
            "Call ONLY when processing an exchange."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Product SKU, e.g. 'P007-9' or 'P003-M'",
                },
            },
            "required": ["sku"],
        },
    },
    {
        "type": "function",
        "name": "calculate_resolution",
        "description": (
            "Calculate financial details for a resolution plan. Takes a list of "
            "item actions with item_id, action (refund/exchange/replacement/"
            "store_credit/deny/shipping_credit), reason, and optionally "
            "exchange_sku. Returns per-item breakdown and totals. "
            "Always call check_resolution_policy FIRST."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID"},
                "items": {
                    "type": "array",
                    "description": "List of item resolution actions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "action": {
                                "type": "string",
                                "enum": [
                                    "refund", "exchange", "replacement",
                                    "store_credit", "deny", "shipping_credit",
                                ],
                            },
                            "reason": {"type": "string"},
                            "exchange_sku": {"type": "string"},
                        },
                        "required": ["item_id", "action", "reason"],
                    },
                },
            },
            "required": ["order_id", "items"],
        },
    },
    {
        "type": "function",
        "name": "submit_resolution",
        "description": (
            "Submit the final resolution for processing. Returns a confirmation "
            "ID. ONLY call after calculate_resolution confirms the amounts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID"},
                "resolution_summary": {
                    "type": "string",
                    "description": "Text summary of the resolution being submitted",
                },
            },
            "required": ["order_id", "resolution_summary"],
        },
    },
]

TOOL_FUNCTIONS = {
    "get_order_details": get_order_details,
    "get_fulfillment_status": get_fulfillment_status,
    "check_resolution_policy": check_resolution_policy,
    "check_inventory": check_inventory,
    "calculate_resolution": calculate_resolution,
    "submit_resolution": submit_resolution,
}
