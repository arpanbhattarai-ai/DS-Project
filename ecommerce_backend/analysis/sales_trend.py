"""
analysis/sales_trend.py  -  Monthly Sales Revenue Trend
"""
from logger import get_logger

logger = get_logger(__name__)

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_label(month_num) -> str:
    try:
        n = int(month_num)
    except (TypeError, ValueError):
        return "Unknown"
    return MONTH_ABBR[n - 1] if 1 <= n <= 12 else "Unknown"


def _with_month_names(df):
    out = df.copy()
    out["MonthName"] = out["MonthNum"].apply(_month_label)
    return out


def compute_sales_trend(context: dict) -> dict:
    sales = context["sales"]

    monthly_revenue = (
        sales.assign(Revenue=sales["QuantitySold"] * sales["UnitPriceSold"])
        .groupby("MonthNum", as_index=False)["Revenue"]
        .sum()
        .sort_values("MonthNum")
    )
    monthly_revenue = _with_month_names(monthly_revenue)

    by_payment = []
    if "PaymentMode" in sales.columns:
        payment_df = (
            sales.assign(Revenue=sales["QuantitySold"] * sales["UnitPriceSold"])
            .groupby(["MonthNum", "PaymentMode"], as_index=False)["Revenue"]
            .sum()
            .sort_values(["MonthNum", "Revenue"], ascending=[True, False])
        )
        payment_df = _with_month_names(payment_df)
        by_payment = payment_df.rename(columns={"Revenue": "revenue_npr"}).to_dict(orient="records")

    by_delivery = []
    if "DeliveryType" in sales.columns:
        delivery_df = (
            sales.assign(Revenue=sales["QuantitySold"] * sales["UnitPriceSold"])
            .groupby(["MonthNum", "DeliveryType"], as_index=False)["Revenue"]
            .sum()
            .sort_values(["MonthNum", "Revenue"], ascending=[True, False])
        )
        delivery_df = _with_month_names(delivery_df)
        by_delivery = delivery_df.rename(columns={"Revenue": "revenue_npr"}).to_dict(orient="records")

    total_revenue = float((sales["QuantitySold"] * sales["UnitPriceSold"]).sum())
    result = {
        "total_sales_revenue_npr": round(total_revenue, 2),
        "monthly_sales_revenue": monthly_revenue.rename(columns={"Revenue": "revenue_npr"}).to_dict(orient="records"),
        "monthly_by_payment_mode": by_payment,
        "monthly_by_delivery_type": by_delivery,
    }

    context.setdefault("analysis", {})["sales_trend"] = result
    logger.info("Sales trend metrics computed.")
    return result
