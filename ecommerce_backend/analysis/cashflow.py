"""
analysis/cashflow.py  -  Section 9: Cash Flow
"""
from logger import get_logger
logger = get_logger(__name__)


def compute_cashflow(store: dict) -> dict:
    sales = store["sales"]
    purch = store["purch"]
    v     = store["vars"]

    TotalCashInflow  = v["TotalRevenue"]
    TotalCashOutflow = v["TotalPurchaseCost"] + v["TotalOperatingExpense"]
    NetCashMovement  = TotalCashInflow - TotalCashOutflow

    monthly_in  = sales.groupby("MonthNum").apply(
        lambda d: (d["QuantitySold"] * d["UnitPriceSold"]).sum() - d["Discount"].sum()
    ).rename("CashIn").reset_index()

    monthly_out = purch.groupby("Month").apply(
        lambda d: (d["QuantityBought"] * d["UnitCost"]).sum()
    ).rename("CashOut").reset_index().rename(columns={"Month": "MonthNum"})

    monthly_cf = monthly_in.merge(monthly_out, on="MonthNum", how="left").fillna(0)
    monthly_cf["NetCash"] = monthly_cf["CashIn"] - monthly_cf["CashOut"]

    logger.info(f"Cashflow: NetCashMovement={NetCashMovement:,.0f}")
    return {
        "total_cash_inflow_npr":  round(TotalCashInflow, 2),
        "total_cash_outflow_npr": round(TotalCashOutflow, 2),
        "net_cash_movement_npr":  round(NetCashMovement, 2),
        "monthly_cashflow": monthly_cf[["MonthNum","CashIn","CashOut","NetCash"]].round(2).to_dict(orient="records"),
    }
