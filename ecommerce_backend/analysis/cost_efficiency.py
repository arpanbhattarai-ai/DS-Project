"""
analysis/cost_efficiency.py  -  Expense vs Purchase Cost Trend
"""
from logger import get_logger

logger = get_logger(__name__)

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
EXP_COLS = ["Salary", "Rent", "Utilities", "Marketing", "EMI", "Interest", "Other"]


def _month_num_from_purchase(value):
    try:
        n = int(value)
        return n if 1 <= n <= 12 else None
    except (TypeError, ValueError):
        return None


def _month_num_from_expense(value):
    lookup = {name: i + 1 for i, name in enumerate(MONTH_NAMES)}
    return lookup.get(value)


def compute_cost_efficiency(context: dict) -> dict:
    purch = context["purch"]
    exp = context["exp"]

    purchase_monthly = (
        purch.assign(
            MonthNum=purch["Month"].apply(_month_num_from_purchase),
            PurchaseCost=purch["QuantityBought"] * purch["UnitCost"],
        )
        .dropna(subset=["MonthNum"])
        .groupby("MonthNum", as_index=False)["PurchaseCost"]
        .sum()
    )

    expense_monthly = (
        exp.assign(
            MonthNum=exp["Month"].apply(_month_num_from_expense),
            OperatingExpense=exp[[c for c in EXP_COLS if c in exp.columns]].sum(axis=1),
        )
        .dropna(subset=["MonthNum"])
        .groupby("MonthNum", as_index=False)["OperatingExpense"]
        .sum()
    )

    merged = purchase_monthly.merge(expense_monthly, on="MonthNum", how="outer").fillna(0)
    merged["MonthNum"] = merged["MonthNum"].astype(int)
    merged = merged.sort_values("MonthNum")
    merged["Month"] = merged["MonthNum"].apply(lambda n: MONTH_NAMES[n - 1])
    merged["MonthName"] = merged["MonthNum"].apply(lambda n: MONTH_ABBR[n - 1])

    merged["TotalCost"] = merged["PurchaseCost"] + merged["OperatingExpense"]
    merged["ExpenseToPurchaseRatio"] = merged["OperatingExpense"] / merged["PurchaseCost"].replace(0, 1)

    result = {
        "summary": {
            "total_purchase_cost_npr": round(float(merged["PurchaseCost"].sum()), 2),
            "total_operating_expense_npr": round(float(merged["OperatingExpense"].sum()), 2),
            "total_combined_cost_npr": round(float(merged["TotalCost"].sum()), 2),
        },
        "monthly_cost_efficiency": (
            merged[
                ["Month", "MonthName", "PurchaseCost", "OperatingExpense", "TotalCost", "ExpenseToPurchaseRatio"]
            ]
            .round(2)
            .rename(
                columns={
                    "PurchaseCost": "purchase_cost_npr",
                    "OperatingExpense": "operating_expense_npr",
                    "TotalCost": "total_cost_npr",
                    "ExpenseToPurchaseRatio": "expense_to_purchase_ratio",
                }
            )
            .to_dict(orient="records")
        ),
    }

    context.setdefault("analysis", {})["cost_efficiency"] = result
    logger.info("Cost efficiency metrics computed.")
    return result
