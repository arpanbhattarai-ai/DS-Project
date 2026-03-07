"""
analysis/demand_vs_stock.py  -  Stock vs Sales Demand Analysis
"""
from logger import get_logger

logger = get_logger(__name__)


def compute_demand_vs_stock(context: dict) -> dict:
    inv = context["inv"].copy()
    sales = context["sales"]

    demand = (
        sales.groupby("ItemID", as_index=False)["QuantitySold"]
        .sum()
        .rename(columns={"QuantitySold": "TotalDemand"})
    )

    detail = inv.merge(demand, on="ItemID", how="left")
    detail["TotalDemand"] = detail["TotalDemand"].fillna(0)
    detail["OpeningStock"] = detail["OpeningStock"].fillna(0)
    detail["DemandStockRatio"] = detail["TotalDemand"] / detail["OpeningStock"].replace(0, 1)
    detail["GapQty"] = detail["OpeningStock"] - detail["TotalDemand"]

    overstock = detail[(detail["OpeningStock"] > 0) & (detail["DemandStockRatio"] < 0.25)].copy()
    stockout_risk = detail[(detail["OpeningStock"] > 0) & (detail["DemandStockRatio"] >= 0.85)].copy()

    summary = {
        "items_tracked": int(len(detail)),
        "overstock_items": int(len(overstock)),
        "stockout_risk_items": int(len(stockout_risk)),
        "total_opening_stock_units": float(detail["OpeningStock"].sum()),
        "total_sales_demand_units": float(detail["TotalDemand"].sum()),
    }

    result = {
        "summary": summary,
        "detail": (
            detail[
                ["ItemID", "ItemName", "Category", "OpeningStock", "TotalDemand", "DemandStockRatio", "GapQty"]
            ]
            .round(2)
            .to_dict(orient="records")
        ),
        "overstock_items": (
            overstock[
                ["ItemID", "ItemName", "Category", "OpeningStock", "TotalDemand", "DemandStockRatio", "GapQty"]
            ]
            .sort_values(["DemandStockRatio", "OpeningStock"], ascending=[True, False])
            .head(25)
            .round(2)
            .to_dict(orient="records")
        ),
        "stockout_risk_items": (
            stockout_risk[
                ["ItemID", "ItemName", "Category", "OpeningStock", "TotalDemand", "DemandStockRatio", "GapQty"]
            ]
            .sort_values(["DemandStockRatio", "TotalDemand"], ascending=[False, False])
            .head(25)
            .round(2)
            .to_dict(orient="records")
        ),
    }

    context.setdefault("analysis", {})["demand_vs_stock"] = result
    logger.info("Demand vs stock metrics computed.")
    return result
