from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from configs.settings import TEST_DATA
from utils.payload_pruner import prune_payload


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def unique_suffix() -> str:
    return uuid4().hex[:10]


def crm_customer_payload() -> dict:
    suffix = unique_suffix()
    return prune_payload(
        {
            "customers": [
                {
                    "website_id": f"autotest-{suffix}",
                    "email": f"autotest.{suffix}@example.com",
                    "first_name": "API",
                    "last_name": "Autotest",
                    "custom_fields": [
                        {
                            "system_name": "ticket_number",
                            "field_value": f"TICKET-{suffix}",
                        }
                    ],
                }
            ]
        }
    )


def crm_customer_update_payload(customer_id: int) -> dict:
    return prune_payload(
        {
            "customers": [
                {
                    "id": customer_id,
                    "first_name": "Updated",
                    "custom_fields": [
                        {
                            "system_name": "semeynoe_polozhenie",
                            "field_value": "single",
                        }
                    ],
                }
            ]
        }
    )


def crm_customer_search_payload() -> dict:
    return prune_payload(
        {
            "filter": {
                "email": TEST_DATA.email,
            },
            "page": 1,
            "page_size": 1,
        }
    )


def crm_customer_action_payload() -> dict:
    suffix = unique_suffix()
    return prune_payload(
        {
            "customer_id": TEST_DATA.customer_id,
            "action_template_system_name": TEST_DATA.action_template_system_name,
            "event_time": utc_now(),
            "external_action_id": f"autotest-action-{suffix}",
            "description": "Autotest customer action",
        }
    )


def crm_customer_action_bulk_payload() -> dict:
    first = crm_customer_action_payload()
    second = crm_customer_action_payload()
    return {"actions": [first, second]}


def accounting_product_payload() -> dict:
    suffix = unique_suffix()
    return prune_payload(
        {
            "external_id": f"autotest-product-{suffix}",
            "external_system": "Ecom",
            "name": f"Autotest Product {suffix}",
            "price": 100.0,
            "category": {
                "external_id": "autotest-category",
                "name": "Autotest category",
            },
            "custom_fields": [
                {
                    "system_name": "camelCaseNumber1",
                    "field_value": "true",
                }
            ],
        }
    )


def accounting_bulk_product_payload() -> dict:
    first = accounting_product_payload()
    second = accounting_product_payload()
    return {"items": [first, second]}


def accounting_order_payload() -> dict:
    suffix = unique_suffix()
    return prune_payload(
        {
            "external_order_id": f"autotest-order-{suffix}",
            "external_system": "Ecom",
            "website_id": TEST_DATA.website_id,
            "email": TEST_DATA.email,
            "mobile_phone": TEST_DATA.mobile_phone,
            "status": "cart",
            "items": [
                {
                    "external_line_id": "line-1",
                    "position_number": 1,
                    "external_product_id": "autotest-product-line",
                    "product_name": "Autotest line",
                    "unit_price": 100.0,
                    "quantity": 1,
                }
            ],
            "totals": {
                "subtotal": 100.0,
                "total": 100.0,
            },
        }
    )


def accounting_order_update_payload(contact_point_id: str) -> dict:
    return prune_payload(
        {
            "status": "new",
            "contact_point_id": contact_point_id,
        }
    )


def accounting_calculate_payload() -> dict:
    suffix = unique_suffix()
    return prune_payload(
        {
            "website_id": TEST_DATA.website_id,
            "order": {
                "external_order_id": f"autotest-calc-{suffix}",
                "external_system": "TICKET_SYSTEM",
                "items": [
                    {
                        "external_line_id": "line-1",
                        "position_number": 1,
                        "external_product_id": "calc-product-1",
                        "product_name": "Autotest calculate line",
                        "unit_price": 100.0,
                        "quantity": 1,
                    }
                ],
            },
        }
    )


def accounting_promotion_preview_payload(order_id: int) -> dict:
    return {
        "order_id": order_id,
    }
