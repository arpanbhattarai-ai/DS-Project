from django.conf import settings
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from .services import fetch_dashboard_payload

VALID_PERIODS = {"monthly", "quarterly", "semiannual", "annual"}
PERIOD_BUCKETS = {
    "monthly": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "quarterly": ["Q1", "Q2", "Q3", "Q4"],
    "semiannual": ["H1", "H2"],
    "annual": ["Year"],
}


@never_cache
def dashboard_view(request):
    selected_period = (request.GET.get("period") or "monthly").strip().lower()
    if selected_period not in VALID_PERIODS:
        selected_period = "monthly"

    selected_bucket = (request.GET.get("bucket") or "all").strip()
    bucket_options = PERIOD_BUCKETS[selected_period]
    if selected_bucket != "all" and selected_bucket not in bucket_options:
        selected_bucket = "all"

    payload, errors = fetch_dashboard_payload(
        selected_period,
        None if selected_bucket == "all" else selected_bucket,
    )

    profitability = payload.get("profitability", {})
    discounts = payload.get("discounts", {})
    inventory = payload.get("inventory", {})
    expenses = payload.get("expenses", {})
    breakeven = payload.get("breakeven", {})
    cashflow = payload.get("cashflow", {})
    products = payload.get("products", {})
    monthly_growth = payload.get("monthly_growth", {})

    context = {
        "kpis": [
            {"label": "Net Revenue", "value": profitability.get("net_revenue_npr"), "prefix": "NPR "},
            {"label": "Net Profit", "value": profitability.get("net_profit_npr"), "prefix": "NPR "},
            {
                "label": "Net Profit Margin",
                "value": profitability.get("net_profit_margin_pct"),
                "suffix": "%",
            },
            {
                "label": "Cash Movement",
                "value": cashflow.get("net_cash_movement_npr"),
                "prefix": "NPR ",
            },
            {
                "label": "Inventory Turnover",
                "value": inventory.get("inventory_turnover"),
                "suffix": "x",
            },
            {
                "label": "Reorder Alerts",
                "value": inventory.get("items_below_reorder_level"),
            },
        ],
        "profitability": profitability,
        "discounts": discounts,
        "inventory": inventory,
        "expenses": expenses,
        "breakeven": breakeven,
        "cashflow": cashflow,
        "products": products,
        "monthly_growth": monthly_growth,
        "discount_monthly": discounts.get("monthly_discount", []),
        "category_revenue": products.get("revenue_by_category", []),
        "monthly_expenses": expenses.get("monthly_expenses", []),
        "monthly_growth_data": monthly_growth.get("monthly", []),
        "monthly_cashflow_data": cashflow.get("monthly_cashflow", []),
        "expense_breakdown_data": expenses.get("expense_breakdown", {}),
        "reorder_items": inventory.get("below_reorder_items", []),
        "breakeven_items": breakeven.get("top_20_easiest_breakeven", []),
        "api_base": settings.FASTAPI_BASE_URL.rstrip("/"),
        "errors": errors,
        "selected_period": selected_period,
        "selected_bucket": selected_bucket,
        "bucket_options": bucket_options,
        "has_data_errors": bool(errors),
        "backend_payload_data": payload,
        "backend_errors_data": errors,
    }

    return render(request, "dashboard/index.html", context)
