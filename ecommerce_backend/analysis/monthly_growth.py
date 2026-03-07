"""
analysis/monthly_growth.py  -  Section 7: Monthly Growth Metrics
"""
import numpy as np
from logger import get_logger
logger = get_logger(__name__)

EXP_COLS    = ["Salary", "Rent", "Utilities", "Marketing", "EMI", "Interest", "Other"]
MONTH_ABBR  = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]


def compute_monthly_growth(store: dict) -> dict:
    sales = store["sales"]
    exp   = store["exp"]
    v     = store["vars"]

    monthly_rev = (
        sales.groupby("MonthNum").apply(lambda d: (d["QuantitySold"] * d["UnitPriceSold"]).sum() - d["Discount"].sum())
             .rename("MonthRevenue").reset_index().sort_values("MonthNum")
    )

    exp2 = exp.copy()
    exp2["MonthNum"]     = exp2["Month"].map({m: i+1 for i, m in enumerate(MONTH_NAMES)})
    exp2["TotalExpense"] = exp2[[c for c in EXP_COLS if c in exp2.columns]].sum(axis=1)

    m = monthly_rev.merge(exp2[["MonthNum", "TotalExpense"]], on="MonthNum", how="left")
    m["MonthCOGS"]   = (m["MonthRevenue"] / v["TotalRevenue"]) * v["COGS"]
    m["MonthProfit"] = m["MonthRevenue"] - m["MonthCOGS"] - m["TotalExpense"]
    m["RevGrowth"]   = m["MonthRevenue"].pct_change() * 100
    m["ProfGrowth"]  = m["MonthProfit"].pct_change() * 100
    m["MonthName"]   = [MONTH_ABBR[i-1] for i in m["MonthNum"]]
    m = m.replace([np.inf, -np.inf], None).where(m.notna(), None)

    logger.info("Monthly growth computed.")
    return {"monthly": m[["MonthName","MonthRevenue","MonthProfit","RevGrowth","ProfGrowth"]].round(2).to_dict(orient="records")}
