"""Zava Retail Tools – Azure Function App for agentic RFT training."""
import json
import re
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    import azure.functions as func
    from azure.functions import AsgiFunctionApp
    HAS_AZ = True
except ImportError:
    HAS_AZ = False

# ---------------------------------------------------------------------------
# In-memory database (embedded from zava_db.json)
# ---------------------------------------------------------------------------
TODAY = datetime(2026, 7, 15)
TODAY_STR = "2026-07-15"

DB = {
    "customers": {
        "C001": {"id": "C001", "name": "Sofia Martinez", "email": "sofia.martinez@example.com", "loyalty_tier": "platinum"},
        "C002": {"id": "C002", "name": "Ava Chen", "email": "ava.chen@example.com", "loyalty_tier": "standard"},
        "C003": {"id": "C003", "name": "Yusuf Rossi", "email": "yusuf.rossi@example.com", "loyalty_tier": "gold"},
        "C004": {"id": "C004", "name": "Emma Kim", "email": "emma.kim@example.com", "loyalty_tier": "standard"},
        "C005": {"id": "C005", "name": "Noah Brown", "email": "noah.brown@example.com", "loyalty_tier": "platinum"},
    },
    "products": {
        "P001": {"id": "P001", "name": "Wireless Headphones", "category": "electronics", "price": 149.99, "on_sale": False},
        "P002": {"id": "P002", "name": "Mechanical Keyboard", "category": "electronics", "price": 129.99, "on_sale": False,
                 "variants": [{"sku": "P002-BLK", "variant": "Black"}, {"sku": "P002-WHT", "variant": "White"}, {"sku": "P002-RGB", "variant": "RGB"}]},
        "P002-BLK": {"id": "P002", "name": "Mechanical Keyboard", "category": "electronics", "price": 129.99, "on_sale": False, "selected_variant": "Black",
                     "variants": [{"sku": "P002-BLK", "variant": "Black"}, {"sku": "P002-WHT", "variant": "White"}, {"sku": "P002-RGB", "variant": "RGB"}]},
        "P002-WHT": {"id": "P002", "name": "Mechanical Keyboard", "category": "electronics", "price": 129.99, "on_sale": False, "selected_variant": "White",
                     "variants": [{"sku": "P002-BLK", "variant": "Black"}, {"sku": "P002-WHT", "variant": "White"}, {"sku": "P002-RGB", "variant": "RGB"}]},
        "P002-RGB": {"id": "P002", "name": "Mechanical Keyboard", "category": "electronics", "price": 129.99, "on_sale": False, "selected_variant": "RGB",
                     "variants": [{"sku": "P002-BLK", "variant": "Black"}, {"sku": "P002-WHT", "variant": "White"}, {"sku": "P002-RGB", "variant": "RGB"}]},
        "P003": {"id": "P003", "name": "Smart Watch", "category": "electronics", "price": 299.99, "on_sale": False,
                 "variants": [{"sku": "P003-S", "variant": "Small"}, {"sku": "P003-M", "variant": "Medium"}, {"sku": "P003-L", "variant": "Large"}]},
        "P003-S": {"id": "P003", "name": "Smart Watch", "category": "electronics", "price": 299.99, "on_sale": False, "selected_variant": "Small",
                   "variants": [{"sku": "P003-S", "variant": "Small"}, {"sku": "P003-M", "variant": "Medium"}, {"sku": "P003-L", "variant": "Large"}]},
        "P003-M": {"id": "P003", "name": "Smart Watch", "category": "electronics", "price": 299.99, "on_sale": False, "selected_variant": "Medium",
                   "variants": [{"sku": "P003-S", "variant": "Small"}, {"sku": "P003-M", "variant": "Medium"}, {"sku": "P003-L", "variant": "Large"}]},
        "P003-L": {"id": "P003", "name": "Smart Watch", "category": "electronics", "price": 299.99, "on_sale": False, "selected_variant": "Large",
                   "variants": [{"sku": "P003-S", "variant": "Small"}, {"sku": "P003-M", "variant": "Medium"}, {"sku": "P003-L", "variant": "Large"}]},
        "P004": {"id": "P004", "name": "Bluetooth Speaker", "category": "electronics", "price": 79.99, "on_sale": False},
        "P005": {"id": "P005", "name": "Electric Kettle", "category": "electronics", "price": 59.99, "on_sale": False},
        "P006": {"id": "P006", "name": "Merino Wool Sweater", "category": "apparel", "price": 89.99, "on_sale": False,
                 "variants": [{"sku": "P006-S", "variant": "Small"}, {"sku": "P006-M", "variant": "Medium"}, {"sku": "P006-L", "variant": "Large"}, {"sku": "P006-XL", "variant": "XL"}]},
        "P006-S": {"id": "P006", "name": "Merino Wool Sweater", "category": "apparel", "price": 89.99, "on_sale": False, "selected_variant": "Small",
                   "variants": [{"sku": "P006-S", "variant": "Small"}, {"sku": "P006-M", "variant": "Medium"}, {"sku": "P006-L", "variant": "Large"}, {"sku": "P006-XL", "variant": "XL"}]},
        "P006-M": {"id": "P006", "name": "Merino Wool Sweater", "category": "apparel", "price": 89.99, "on_sale": False, "selected_variant": "Medium",
                   "variants": [{"sku": "P006-S", "variant": "Small"}, {"sku": "P006-M", "variant": "Medium"}, {"sku": "P006-L", "variant": "Large"}, {"sku": "P006-XL", "variant": "XL"}]},
        "P006-L": {"id": "P006", "name": "Merino Wool Sweater", "category": "apparel", "price": 89.99, "on_sale": False, "selected_variant": "Large",
                   "variants": [{"sku": "P006-S", "variant": "Small"}, {"sku": "P006-M", "variant": "Medium"}, {"sku": "P006-L", "variant": "Large"}, {"sku": "P006-XL", "variant": "XL"}]},
        "P006-XL": {"id": "P006", "name": "Merino Wool Sweater", "category": "apparel", "price": 89.99, "on_sale": False, "selected_variant": "XL",
                    "variants": [{"sku": "P006-S", "variant": "Small"}, {"sku": "P006-M", "variant": "Medium"}, {"sku": "P006-L", "variant": "Large"}, {"sku": "P006-XL", "variant": "XL"}]},
        "P007": {"id": "P007", "name": "Trail Hiking Boots", "category": "apparel", "price": 159.99, "on_sale": False,
                 "variants": [{"sku": "P007-9", "variant": "Size 9"}, {"sku": "P007-10", "variant": "Size 10"}, {"sku": "P007-11", "variant": "Size 11"}]},
        "P007-9": {"id": "P007", "name": "Trail Hiking Boots", "category": "apparel", "price": 159.99, "on_sale": False, "selected_variant": "Size 9",
                   "variants": [{"sku": "P007-9", "variant": "Size 9"}, {"sku": "P007-10", "variant": "Size 10"}, {"sku": "P007-11", "variant": "Size 11"}]},
        "P007-10": {"id": "P007", "name": "Trail Hiking Boots", "category": "apparel", "price": 159.99, "on_sale": False, "selected_variant": "Size 10",
                    "variants": [{"sku": "P007-9", "variant": "Size 9"}, {"sku": "P007-10", "variant": "Size 10"}, {"sku": "P007-11", "variant": "Size 11"}]},
        "P007-11": {"id": "P007", "name": "Trail Hiking Boots", "category": "apparel", "price": 159.99, "on_sale": False, "selected_variant": "Size 11",
                    "variants": [{"sku": "P007-9", "variant": "Size 9"}, {"sku": "P007-10", "variant": "Size 10"}, {"sku": "P007-11", "variant": "Size 11"}]},
        "P008": {"id": "P008", "name": "Running Jacket", "category": "apparel", "price": 119.99, "on_sale": False},
        "P009": {"id": "P009", "name": "LED Desk Lamp", "category": "electronics", "price": 45.99, "on_sale": False},
        "P010": {"id": "P010", "name": "Premium Yoga Mat", "category": "home", "price": 69.99, "on_sale": False},
        "P011": {"id": "P011", "name": "Canvas Tote Bag", "category": "apparel", "price": 34.99, "on_sale": False},
        "P012": {"id": "P012", "name": "Face Serum Set", "category": "personal_care", "price": 89.99, "on_sale": False},
        "P013": {"id": "P013", "name": "Urban Sneakers", "category": "apparel", "price": 64.99, "on_sale": True},
        "P014": {"id": "P014", "name": "Stainless Water Bottle", "category": "home", "price": 24.99, "on_sale": True},
        "P015": {"id": "P015", "name": "Hair Styling Kit", "category": "personal_care", "price": 49.99, "on_sale": False},
    },
    "orders": {
        "ORD-001": {
            "order_id": "ORD-001", "customer_id": "C001", "order_date": "2026-06-28", "promised_delivery": "2026-07-03",
            "line_items": [
                {"item_id": "LI-001", "product_id": "P006", "sku": "P006-M", "name": "Merino Wool Sweater", "category": "apparel", "qty": 1, "unit_price": 89.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 89.99, "tax": 7.20, "total": 97.19, "payment_method": "credit_card",
            "fulfillment": {
                "LI-001": {"status": "delivered", "ship_date": "2026-07-01", "delivery_date": "2026-07-05", "promised_delivery_date": "2026-07-03", "carrier": "FedEx", "late_delivery": False},
            },
        },
        "ORD-002": {
            "order_id": "ORD-002", "customer_id": "C002", "order_date": "2026-05-30", "promised_delivery": "2026-06-05",
            "line_items": [
                {"item_id": "LI-002", "product_id": "P001", "sku": "P001", "name": "Wireless Headphones", "category": "electronics", "qty": 1, "unit_price": 149.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 149.99, "tax": 12.00, "total": 161.99, "payment_method": "credit_card",
            "fulfillment": {
                "LI-002": {"status": "delivered", "ship_date": "2026-06-03", "delivery_date": "2026-06-10", "promised_delivery_date": "2026-06-05", "carrier": "UPS", "late_delivery": True},
            },
        },
        "ORD-003": {
            "order_id": "ORD-003", "customer_id": "C003", "order_date": "2026-06-18", "promised_delivery": "2026-06-23",
            "line_items": [
                {"item_id": "LI-003", "product_id": "P002", "sku": "P002-BLK", "name": "Mechanical Keyboard", "category": "electronics", "qty": 1, "unit_price": 129.99, "discount_pct": 0, "variant": ""},
                {"item_id": "LI-004", "product_id": "P013", "sku": "P013", "name": "Urban Sneakers", "category": "apparel", "qty": 1, "unit_price": 64.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 194.98, "tax": 15.60, "total": 210.58, "payment_method": "debit_card",
            "fulfillment": {
                "LI-003": {"status": "delivered", "ship_date": "2026-06-21", "delivery_date": "2026-06-25", "promised_delivery_date": "2026-06-23", "carrier": "FedEx", "late_delivery": False},
                "LI-004": {"status": "delivered", "ship_date": "2026-06-21", "delivery_date": "2026-06-25", "promised_delivery_date": "2026-06-23", "carrier": "FedEx", "late_delivery": False},
            },
        },
        "ORD-004": {
            "order_id": "ORD-004", "customer_id": "C004", "order_date": "2026-06-30", "promised_delivery": "2026-07-05",
            "line_items": [
                {"item_id": "LI-005", "product_id": "P009", "sku": "P009", "name": "LED Desk Lamp", "category": "electronics", "qty": 1, "unit_price": 45.99, "discount_pct": 0, "variant": ""},
                {"item_id": "LI-006", "product_id": "P012", "sku": "P012", "name": "Face Serum Set", "category": "personal_care", "qty": 1, "unit_price": 89.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 135.98, "tax": 10.88, "total": 146.86, "payment_method": "credit_card",
            "fulfillment": {
                "LI-005": {"status": "delivered", "ship_date": "2026-07-03", "delivery_date": "2026-07-08", "promised_delivery_date": "2026-07-05", "carrier": "USPS", "late_delivery": True},
                "LI-006": {"status": "delivered", "ship_date": "2026-07-03", "delivery_date": "2026-07-08", "promised_delivery_date": "2026-07-05", "carrier": "USPS", "late_delivery": True},
            },
        },
        "ORD-005": {
            "order_id": "ORD-005", "customer_id": "C005", "order_date": "2026-05-15", "promised_delivery": "2026-05-22",
            "line_items": [
                {"item_id": "LI-007", "product_id": "P003", "sku": "P003-M", "name": "Smart Watch", "category": "electronics", "qty": 1, "unit_price": 299.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 299.99, "tax": 24.00, "total": 323.99, "payment_method": "credit_card",
            "fulfillment": {
                "LI-007": {"status": "delivered", "ship_date": "2026-05-19", "delivery_date": "2026-05-26", "promised_delivery_date": "2026-05-22", "carrier": "FedEx", "late_delivery": True},
            },
        },
        "ORD-006": {
            "order_id": "ORD-006", "customer_id": "C002", "order_date": "2026-06-20", "promised_delivery": "2026-06-25",
            "line_items": [
                {"item_id": "LI-008", "product_id": "P010", "sku": "P010", "name": "Premium Yoga Mat", "category": "home", "qty": 1, "unit_price": 69.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 69.99, "tax": 5.60, "total": 75.59, "payment_method": "paypal",
            "fulfillment": {
                "LI-008": {"status": "lost", "ship_date": "2026-06-22", "delivery_date": None, "promised_delivery_date": "2026-06-25", "carrier": "USPS", "late_delivery": False},
            },
        },
        "ORD-007": {
            "order_id": "ORD-007", "customer_id": "C003", "order_date": "2026-05-28", "promised_delivery": "2026-06-02",
            "line_items": [
                {"item_id": "LI-009", "product_id": "P008", "sku": "P008", "name": "Running Jacket", "category": "apparel", "qty": 1, "unit_price": 119.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 119.99, "tax": 9.60, "total": 129.59, "payment_method": "credit_card",
            "fulfillment": {
                "LI-009": {"status": "delivered", "ship_date": "2026-06-01", "delivery_date": "2026-06-05", "promised_delivery_date": "2026-06-02", "carrier": "FedEx", "late_delivery": False},
            },
        },
        "ORD-008": {
            "order_id": "ORD-008", "customer_id": "C001", "order_date": "2026-05-10", "promised_delivery": "2026-05-18",
            "line_items": [
                {"item_id": "LI-010", "product_id": "P005", "sku": "P005", "name": "Electric Kettle", "category": "electronics", "qty": 1, "unit_price": 59.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 59.99, "tax": 4.80, "total": 64.79, "payment_method": "credit_card",
            "fulfillment": {
                "LI-010": {"status": "delivered", "ship_date": "2026-05-14", "delivery_date": "2026-05-21", "promised_delivery_date": "2026-05-18", "carrier": "UPS", "late_delivery": False},
            },
        },
        "ORD-009": {
            "order_id": "ORD-009", "customer_id": "C004", "order_date": "2026-07-01", "promised_delivery": "2026-07-05",
            "line_items": [
                {"item_id": "LI-011", "product_id": "P014", "sku": "P014", "name": "Stainless Water Bottle", "category": "home", "qty": 1, "unit_price": 24.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 24.99, "tax": 2.00, "total": 26.99, "payment_method": "credit_card",
            "fulfillment": {
                "LI-011": {"status": "delivered", "ship_date": "2026-07-03", "delivery_date": "2026-07-05", "promised_delivery_date": "2026-07-05", "carrier": "FedEx", "late_delivery": False},
            },
        },
        "ORD-010": {
            "order_id": "ORD-010", "customer_id": "C005", "order_date": "2026-06-25", "promised_delivery": "2026-06-30",
            "line_items": [
                {"item_id": "LI-012", "product_id": "P007", "sku": "P007-10", "name": "Trail Hiking Boots", "category": "apparel", "qty": 1, "unit_price": 159.99, "discount_pct": 0, "variant": ""},
                {"item_id": "LI-013", "product_id": "P004", "sku": "P004", "name": "Bluetooth Speaker", "category": "electronics", "qty": 1, "unit_price": 79.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 239.98, "tax": 19.20, "total": 259.18, "payment_method": "credit_card",
            "fulfillment": {
                "LI-012": {"status": "delivered", "ship_date": "2026-06-28", "delivery_date": "2026-07-03", "promised_delivery_date": "2026-06-30", "carrier": "FedEx", "late_delivery": False},
                "LI-013": {"status": "delivered", "ship_date": "2026-06-28", "delivery_date": "2026-07-03", "promised_delivery_date": "2026-06-30", "carrier": "FedEx", "late_delivery": False},
            },
        },
        "ORD-011": {
            "order_id": "ORD-011", "customer_id": "C002", "order_date": "2026-06-28", "promised_delivery": "2026-07-03",
            "line_items": [
                {"item_id": "LI-014", "product_id": "P015", "sku": "P015", "name": "Hair Styling Kit", "category": "personal_care", "qty": 1, "unit_price": 49.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 49.99, "tax": 4.00, "total": 53.99, "payment_method": "credit_card",
            "fulfillment": {
                "LI-014": {"status": "delivered", "ship_date": "2026-07-01", "delivery_date": "2026-07-05", "promised_delivery_date": "2026-07-03", "carrier": "UPS", "late_delivery": False},
            },
        },
        "ORD-012": {
            "order_id": "ORD-012", "customer_id": "C003", "order_date": "2026-07-14", "promised_delivery": "2026-07-19",
            "line_items": [
                {"item_id": "LI-015", "product_id": "P002", "sku": "P002-WHT", "name": "Mechanical Keyboard", "category": "electronics", "qty": 1, "unit_price": 129.99, "discount_pct": 0, "variant": ""},
                {"item_id": "LI-016", "product_id": "P011", "sku": "P011", "name": "Canvas Tote Bag", "category": "apparel", "qty": 1, "unit_price": 34.99, "discount_pct": 0, "variant": ""},
            ],
            "subtotal": 164.98, "tax": 13.20, "total": 178.18, "payment_method": "credit_card",
            "fulfillment": {
                "LI-015": {"status": "processing", "ship_date": None, "delivery_date": None, "promised_delivery_date": "2026-07-19", "carrier": None, "late_delivery": False},
                "LI-016": {"status": "processing", "ship_date": None, "delivery_date": None, "promised_delivery_date": "2026-07-19", "carrier": None, "late_delivery": False},
            },
        },
    },
    "inventory": {
        "P002-BLK": {"in_stock": True, "quantity": 15},
        "P002-WHT": {"in_stock": True, "quantity": 3},
        "P002-RGB": {"in_stock": False, "quantity": 0, "restock_date": "2026-08-01"},
        "P003-S": {"in_stock": True, "quantity": 8},
        "P003-M": {"in_stock": False, "quantity": 0, "restock_date": "2026-07-25"},
        "P003-L": {"in_stock": True, "quantity": 2},
        "P006-S": {"in_stock": True, "quantity": 20},
        "P006-M": {"in_stock": True, "quantity": 12},
        "P006-L": {"in_stock": False, "quantity": 0, "restock_date": "2026-07-20"},
        "P006-XL": {"in_stock": True, "quantity": 5},
        "P007-9": {"in_stock": True, "quantity": 4},
        "P007-10": {"in_stock": True, "quantity": 6},
        "P007-11": {"in_stock": False, "quantity": 0, "restock_date": "2026-08-15"},
    },
}


# ---------------------------------------------------------------------------
# Policy constants
# ---------------------------------------------------------------------------
RETURN_WINDOWS = {
    "standard": {"apparel": 30, "home": 30, "electronics": 15, "personal_care": 15},
    "gold":     {"apparel": 45, "home": 45, "electronics": 30, "personal_care": 30},
    "platinum": {"apparel": 60, "home": 60, "electronics": 45, "personal_care": 45},
}


def _get_return_window(tier: str, category: str) -> int:
    return RETURN_WINDOWS.get(tier, RETURN_WINDOWS["standard"]).get(category, 30)


def _is_defective(reason: str) -> bool:
    r = reason.lower()
    return any(w in r for w in [
        "defective", "broken", "damaged", "faulty", "malfunction",
        "defect", "cracked", "flicker", "doesn't work", "not working",
        "damaged_in_shipping",
    ])


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def get_order(order_id: str) -> str:
    order = DB["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    customer = DB["customers"].get(order["customer_id"])
    if not customer:
        return json.dumps({"error": f"Customer not found for order {order_id}"})

    enriched_items = []
    for li in order["line_items"]:
        product = DB["products"].get(li["product_id"])
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

    ful_items = []
    for item_id, ful in order.get("fulfillment", {}).items():
        delivery_date = ful.get("delivery_date")
        days_since = None
        if delivery_date:
            days_since = (TODAY - datetime.fromisoformat(delivery_date)).days
        ful_items.append({
            "item_id": item_id,
            "status": ful["status"],
            "ship_date": ful.get("ship_date"),
            "delivery_date": delivery_date,
            "carrier": ful.get("carrier"),
            "late_delivery": ful.get("late_delivery", False),
            "days_since_delivery": days_since,
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
        "fulfillment": ful_items,
        "subtotal": order["subtotal"],
        "tax": order["tax"],
        "total": order["total"],
        "today": TODAY_STR,
        "payment_method": order["payment_method"],
    }, indent=2)


def check_policy(order_id: str, item_id: str, reason: str) -> str:
    order = DB["orders"].get(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    li = next((i for i in order["line_items"] if i["item_id"] == item_id), None)
    if not li:
        return json.dumps({"error": f"Item {item_id} not found in order {order_id}"})

    product = DB["products"].get(li["product_id"])
    customer = DB["customers"].get(order["customer_id"])
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

    # Lost packages
    if is_lost:
        return json.dumps({
            "eligible": True,
            "eligible_actions": ["refund", "replacement"],
            "return_window_days": None,
            "days_since_delivery": None,
            "restocking_fee_pct": 0.0,
            "shipping_credit": 0.0,
            "special_rules": [
                "Lost package: eligible for full replacement or full refund",
                "No return shipment required",
            ],
        }, indent=2)

    # Pending / processing -> cancellation
    if is_processing:
        return json.dumps({
            "eligible": True,
            "eligible_actions": ["refund"],
            "return_window_days": None,
            "days_since_delivery": None,
            "restocking_fee_pct": 0.0,
            "shipping_credit": 0.0,
            "special_rules": [
                "Order not yet shipped: eligible for cancellation and full refund",
            ],
        }, indent=2)

    # Defective items
    if is_defect:
        if on_sale:
            return json.dumps({
                "eligible": True,
                "eligible_actions": ["store_credit"],
                "return_window_days": effective_window,
                "days_since_delivery": days_since,
                "restocking_fee_pct": 0.0,
                "shipping_credit": shipping_credit,
                "special_rules": [
                    "Defective item: eligible regardless of return window",
                    "Sale item exception: defective sale items -> store credit only (not refund)",
                    "No restocking fee for defective items",
                ],
            }, indent=2)
        return json.dumps({
            "eligible": True,
            "eligible_actions": ["refund", "replacement", "exchange", "store_credit"],
            "return_window_days": effective_window,
            "days_since_delivery": days_since,
            "restocking_fee_pct": 0.0,
            "shipping_credit": shipping_credit,
            "special_rules": [
                "Defective item: eligible regardless of return window or sale status",
                "No restocking fee for defective items",
                "Prepaid return label will be provided",
            ],
        }, indent=2)

    # Sale items (non-defective) -> final sale
    if on_sale:
        return json.dumps({
            "eligible": False,
            "eligible_actions": ["deny"],
            "return_window_days": effective_window,
            "days_since_delivery": days_since,
            "restocking_fee_pct": 0.0,
            "shipping_credit": shipping_credit,
            "special_rules": [
                "Sale/clearance item: final sale - no returns or exchanges unless defective",
            ],
            "denial_reason": "Sale items are final sale and cannot be returned unless defective.",
        }, indent=2)

    # Personal care (non-defective)
    if category == "personal_care":
        r_lower = reason.lower()
        is_sealed = any(w in r_lower for w in ["sealed", "unopened", "never opened"])
        if not is_sealed:
            return json.dumps({
                "eligible": False,
                "eligible_actions": ["deny"],
                "return_window_days": effective_window,
                "days_since_delivery": days_since,
                "restocking_fee_pct": 0.0,
                "shipping_credit": shipping_credit,
                "special_rules": [
                    "Personal care item: not returnable once opened unless defective",
                ],
                "denial_reason": "Opened personal care items cannot be returned unless defective.",
            }, indent=2)

    # Check return window
    if days_since is not None and days_since > effective_window:
        rules = [
            f"Return window expired: {days_since} days since delivery, "
            f"window is {effective_window} days ({tier} tier, {category})",
        ]
        if is_late:
            rules.append(
                f"Late delivery extension already applied: base {base_window} + 15 = {effective_window} days"
            )
            rules.append("$10 shipping credit still applies for late delivery")
        return json.dumps({
            "eligible": False,
            "eligible_actions": ["deny"],
            "return_window_days": effective_window,
            "days_since_delivery": days_since,
            "restocking_fee_pct": 0.0,
            "shipping_credit": shipping_credit,
            "special_rules": rules,
            "denial_reason": (
                f"The {effective_window}-day return window has expired "
                f"({days_since} days since delivery)."
            ),
        }, indent=2)

    # Within window -> eligible
    rules = []
    if is_late:
        rules.append(
            f"Late delivery: window extended from {base_window} to {effective_window} days, "
            f"$10 shipping credit applies"
        )
    if tier != "standard":
        rules.append(f"{tier.title()} tier: {effective_window}-day return window for {category}")
    if category == "electronics" and restocking_pct > 0:
        rules.append(
            f"Electronics restocking fee: {restocking_pct}% applies for non-defective returns"
        )

    days_remaining = (effective_window - days_since) if days_since is not None else None

    return json.dumps({
        "eligible": True,
        "eligible_actions": ["refund", "exchange", "store_credit"],
        "return_window_days": effective_window,
        "days_since_delivery": days_since,
        "days_remaining": days_remaining,
        "restocking_fee_pct": restocking_pct,
        "shipping_credit": shipping_credit,
        "special_rules": rules,
    }, indent=2)


def check_inventory(sku: str) -> str:
    inv = DB["inventory"].get(sku)

    if inv is None:
        prefix = sku.rsplit("-", 1)[0] if "-" in sku else sku
        alternatives = {
            k: {"in_stock": v["in_stock"], "quantity": v["quantity"]}
            for k, v in DB["inventory"].items()
            if k.startswith(prefix)
        }
        if alternatives:
            return json.dumps({
                "error": f"SKU {sku} not found in inventory",
                "available_variants": alternatives,
            }, indent=2)
        return json.dumps({"error": f"SKU {sku} not found in inventory"})

    result = {
        "sku": sku,
        "in_stock": inv["in_stock"],
        "quantity": inv["quantity"],
    }
    if not inv["in_stock"]:
        result["restock_date"] = inv.get("restock_date")
        prefix = sku.rsplit("-", 1)[0] if "-" in sku else sku
        result["alternatives"] = [
            {"sku": k, "quantity": v["quantity"]}
            for k, v in DB["inventory"].items()
            if k.startswith(prefix) and k != sku and v["in_stock"]
        ]

    return json.dumps(result, indent=2)


TOOL_DISPATCH = {
    "get_order": get_order,
    "check_policy": check_policy,
    "check_inventory": check_inventory,
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
ACTION_WORDS = {
    "refund", "deny", "denied", "exchange", "store_credit", "store credit",
    "replacement", "cancel", "cancelled", "cancellation", "shipping_credit",
    "shipping credit",
}

AMOUNT_RE = re.compile(r"\$(\d+(?:\.\d{1,2})?)")


def score_response(output_text: str, reference_answer: str) -> float:
    out_lower = output_text.lower()
    ref_lower = reference_answer.lower()

    # 1. Action match (0.4)
    ref_actions = [w for w in ACTION_WORDS if w in ref_lower]
    if ref_actions:
        action_hits = sum(1 for a in ref_actions if a in out_lower)
        action_score = action_hits / len(ref_actions)
    else:
        action_score = 1.0

    # 2. Amount match (0.3)
    ref_amounts = set(AMOUNT_RE.findall(reference_answer))
    if ref_amounts:
        out_amounts = set(AMOUNT_RE.findall(output_text))
        amount_hits = len(ref_amounts & out_amounts)
        amount_score = amount_hits / len(ref_amounts)
    else:
        amount_score = 1.0

    # 3. Policy reason keywords (0.3)
    reason_phrases = []
    for phrase in [
        "restocking", "final sale", "sale item", "window expired", "expired",
        "personal care", "defective", "lost package", "not yet shipped",
        "cancellation", "late delivery", "shipping credit", "platinum",
        "gold", "standard", "store credit", "no restocking", "unopened",
        "sealed",
    ]:
        if phrase in ref_lower:
            reason_phrases.append(phrase)

    if reason_phrases:
        reason_hits = sum(1 for p in reason_phrases if p in out_lower)
        reason_score = reason_hits / len(reason_phrases)
    else:
        reason_score = 1.0

    total = 0.4 * action_score + 0.3 * amount_score + 0.3 * reason_score
    return round(total, 4)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Zava RFT Tools", version="1.0.0")


@app.get("/")
async def health():
    return {"status": "ok", "tools": list(TOOL_DISPATCH.keys()), "today": TODAY_STR}


@app.post("/tool/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    if tool_name not in TOOL_DISPATCH:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unknown tool: {tool_name}. Available: {list(TOOL_DISPATCH.keys())}"},
        )

    body = await request.json()
    call_id = body.get("call_id", "")
    fc_id = body.get("id", "")
    arguments_raw = body.get("arguments", "{}")

    if isinstance(arguments_raw, str):
        try:
            arguments = json.loads(arguments_raw)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON in arguments field"},
            )
    else:
        arguments = arguments_raw

    fn = TOOL_DISPATCH[tool_name]
    try:
        output = fn(**arguments)
    except TypeError as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid arguments for {tool_name}: {e}"},
        )

    return {
        "type": "function_call_output",
        "call_id": call_id,
        "id": fc_id,
        "output": output,
    }


@app.post("/score")
async def score_endpoint(request: Request):
    body = await request.json()
    sample = body.get("sample", {})
    item = body.get("item", {})

    output_text = sample.get("output_text", "")
    reference_answer = item.get("reference_answer", "")

    if not reference_answer:
        return JSONResponse(status_code=400, content={"error": "Missing reference_answer"})

    s = score_response(output_text, reference_answer)
    return {"score": s}


@app.post("/grade")
async def grade_endpoint(request: Request):
    """Endpoint grader for agentic RFT. Robust error handling + logging."""
    import traceback

    try:
        body = await request.json()
    except Exception as e:
        return {"score": 0.0}

    sample = body.get("sample", {})
    item = body.get("item", {})
    trace_id = body.get("trace_id", "")

    try:
        # Get output text — try multiple paths
        output_text = ""
        if isinstance(sample, dict):
            output_text = sample.get("output_text", "") or ""
            # Fallback: check output messages
            if not output_text:
                for msg in reversed(sample.get("output", [])):
                    if isinstance(msg, dict) and msg.get("content"):
                        output_text = msg["content"]
                        break

        # Get expected — support both expected_items and expected_resolution
        expected_resolution = item.get("expected_resolution", "")
        expected_items_str = item.get("expected_items", "")

        # If we have expected_resolution (v5 format), use text-based scoring
        if expected_resolution:
            if not output_text or len(output_text) < 20:
                return {"score": 0.0}
            return {"score": score_response(output_text, expected_resolution)}

        # If we have expected_items (v4 format), use structured scoring
        if expected_items_str:
            try:
                expected_items = json.loads(expected_items_str) if isinstance(expected_items_str, str) else expected_items_str
            except:
                expected_items = []

            if not expected_items:
                return {"score": 0.5}
            if not output_text or len(output_text) < 5:
                return {"score": 0.0}

            # Parse JSON from model output
            parsed = None
            try:
                t = output_text.strip()
                if t.startswith("```"):
                    t = "\n".join(t.split("\n")[1:]).rstrip("`").strip()
                parsed = json.loads(t)
            except:
                m = re.search(r'\{.*\}', output_text, re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group())
                    except:
                        pass

            if not parsed:
                return {"score": 0.0}

            items = parsed.get("items", [parsed] if "action" in parsed else [])
            if not items:
                return {"score": 0.0}

            item_scores = []
            for exp in expected_items:
                best = 0.0
                for act in items:
                    s = 0.0
                    if (act.get("action") or "").lower() == exp.get("action", "").lower():
                        s += 0.35
                    elif (act.get("action") or "").lower() in ("refund", "replacement") and exp.get("action", "").lower() in ("refund", "replacement"):
                        s += 0.15
                    try:
                        a = float(act.get("net_refund", act.get("amount", -999)))
                        e = float(exp.get("net_refund", 0))
                        if abs(a - e) < 0.05: s += 0.30
                        elif abs(a - e) < 2.0: s += 0.15
                        elif e == 0 and a == 0: s += 0.30
                    except: pass
                    if "restocking_fee" in exp:
                        try:
                            a = float(act.get("restocking_fee", -999))
                            e = float(exp["restocking_fee"])
                            if abs(a - e) < 0.05: s += 0.15
                            elif e == 0 and a == 0: s += 0.15
                        except: pass
                    else: s += 0.15
                    if "shipping_credit" in exp:
                        try:
                            a = float(act.get("shipping_credit", 0))
                            e = float(exp["shipping_credit"])
                            if abs(a - e) < 0.05: s += 0.10
                            elif e == 0 and a == 0: s += 0.10
                        except: pass
                    else: s += 0.10
                    if act.get("reason") and len(str(act.get("reason", ""))) > 10: s += 0.10
                    best = max(best, s)
                item_scores.append(best)

            return {"score": round(sum(item_scores) / len(item_scores), 3) if item_scores else 0.0}

        # No expected data at all — give partial credit for any response
        if output_text and len(output_text) > 20:
            return {"score": 0.3}
        return {"score": 0.0}

    except Exception as e:
        # NEVER crash — always return a score
        return {"score": 0.0}


# Debug endpoint to log what the training infra sends
_recent_grade_requests = []

@app.post("/debug_grade")
async def debug_grade_endpoint(request: Request):
    """Same as /grade but logs requests for debugging."""
    body = await request.json()
    _recent_grade_requests.append(json.dumps(body, default=str)[:2000])
    if len(_recent_grade_requests) > 50:
        _recent_grade_requests.pop(0)
    # Forward to the real grade logic
    return await grade_endpoint(request)

@app.get("/debug_logs")
async def get_debug_logs():
    """View recent grade requests."""
    return {"count": len(_recent_grade_requests), "recent": _recent_grade_requests[-10:]}


# ---------------------------------------------------------------------------
# Azure Functions ASGI wrapper
# ---------------------------------------------------------------------------
if HAS_AZ:
    asgi_app = AsgiFunctionApp(app=app, http_auth_level=func.AuthLevel.ANONYMOUS)
