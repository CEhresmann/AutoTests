from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from configs.settings import TEST_DATA
from utils.payload_pruner import prune_payload


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_in(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def crm_campaign_automatic_send_payload(campaign_id: int) -> dict:
    return {
        "campaign_id": campaign_id,
        "customer_ids": [TEST_DATA.customer_id],
    }


def crm_device_payload(device_id: str | None = None) -> dict:
    suffix = device_id or f"autotest-device-{unique_suffix()}"
    return prune_payload(
        {
            "device_id": suffix,
            "device_info": {
                "source": "autotest",
                "user_agent": "pytest",
            },
        }
    )


def crm_device_assign_payload(device_id: str) -> dict:
    return prune_payload(
        {
            "device_id": device_id,
            "customer_id": TEST_DATA.customer_id,
        }
    )


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


def accounting_order_item_update_payload(status: str = "ACTIVE") -> dict:
    return {
        "status": status,
    }


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


def accounting_bonus_accrue_payload() -> dict:
    return prune_payload(
        {
            "customer_id": TEST_DATA.customer_id,
            "amount": 1,
            "description": "Autotest bonus accrue",
            "valid_from": utc_now(),
        }
    )


def accounting_bonus_pending_accrue_payload() -> dict:
    return prune_payload(
        {
            "customer_id": TEST_DATA.customer_id,
            "amount": 1,
            "description": "Autotest pending bonus accrue",
            "valid_from": utc_in(31),
            "valid_until": utc_in(62),
        }
    )


def accounting_bonus_activate_payload(bonus_id: str) -> dict:
    return {
        "bonus_id": bonus_id,
    }


def accounting_bonus_hold_payload(order_external_id: str) -> dict:
    return prune_payload(
        {
            "customer_id": TEST_DATA.customer_id,
            "external_order_id": order_external_id,
            "amount": 1,
            "channel": "WEB",
        }
    )


def accounting_bonus_hold_release_payload() -> dict:
    return {
        "status": "RELEASED",
    }


def accounting_promotion_apply_payload(order_id: int, promocode: str | None = None) -> dict:
    payload = {"order_id": order_id}
    if promocode:
        payload["promocode"] = promocode
    return payload


def accounting_promotion_apply_to_item_payload(order_id: int, order_item_id: int, promotion_id: int) -> dict:
    return {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "promotion_id": promotion_id,
    }


def accounting_promotion_remove_payload(order_id: int, promotion_id: int) -> dict:
    return {
        "order_id": order_id,
        "promotion_id": promotion_id,
    }


def accounting_promotion_available_payload(order_id: int) -> dict:
    return {
        "order_id": order_id,
    }


def accounting_promocode_assign_payload(pool_id: int) -> dict:
    return {
        "pool_id": pool_id,
        "customer_id": TEST_DATA.customer_id,
    }


def accounting_gift_certificate_activate_payload(order_external_id: str) -> dict:
    suffix = unique_suffix()
    return {
        "nominal_value": 1,
        "transaction_id": f"autotest-gift-activate-{suffix}",
        "external_order_id": order_external_id,
        "customer_id": TEST_DATA.customer_id,
        "activated_at": utc_now(),
    }


def accounting_gift_certificate_debit_payload() -> dict:
    suffix = unique_suffix()
    return {
        "amount": 1,
        "transaction_id": f"autotest-gift-debit-{suffix}",
    }


def accounting_gift_certificate_credit_payload() -> dict:
    suffix = unique_suffix()
    return {
        "amount": 1,
        "transaction_id": f"autotest-gift-credit-{suffix}",
    }


def accounting_gift_certificate_refund_payload() -> dict:
    suffix = unique_suffix()
    return {
        "transaction_id": f"autotest-gift-refund-{suffix}",
    }


def accounting_gift_certificate_validate_payload() -> dict:
    suffix = unique_suffix()
    return {
        "transaction_id": f"autotest-gift-validate-{suffix}",
    }
