"""
routes/analysis.py  -  One GET endpoint per BI section.
"""
from fastapi import APIRouter, HTTPException
from logger import get_logger
import state

from analysis.profitability  import compute_profitability
from analysis.discounts      import compute_discounts
from analysis.inventory      import compute_inventory
from analysis.products       import compute_products
from analysis.expenses       import compute_expenses
from analysis.monthly_growth import compute_monthly_growth
from analysis.breakeven      import compute_breakeven
from analysis.cashflow       import compute_cashflow
from analysis.sales_trend    import compute_sales_trend
from analysis.demand_vs_stock import compute_demand_vs_stock
from analysis.cost_efficiency import compute_cost_efficiency

router = APIRouter(prefix="/analysis")
logger = get_logger(__name__)


def _analysis_context() -> dict:
    return {
        "sales": state.store["sales"],
        "purch": state.store["purch"],
        "inv": state.store["inv"],
        "exp": state.store["exp"],
        "analysis": {},
    }


def _require_data():
    if not state.store["ready"]:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Upload a file or place an Excel file in data/raw and restart.",
        )


@router.get("/profitability")
def profitability():
    _require_data()
    return compute_profitability(state.store)


@router.get("/discounts")
def discounts():
    _require_data()
    return compute_discounts(state.store)


@router.get("/inventory")
def inventory():
    _require_data()
    return compute_inventory(state.store)


@router.get("/products")
def products():
    _require_data()
    return compute_products(state.store)


@router.get("/expenses")
def expenses():
    _require_data()
    return compute_expenses(state.store)


@router.get("/monthly-growth")
def monthly_growth():
    _require_data()
    return compute_monthly_growth(state.store)


@router.get("/breakeven")
def breakeven():
    _require_data()
    return compute_breakeven(state.store)


@router.get("/cashflow")
def cashflow():
    _require_data()
    return compute_cashflow(state.store)


@router.get("/sales-trend")
def sales_trend():
    _require_data()
    return compute_sales_trend(_analysis_context())


@router.get("/demand-vs-stock")
def demand_vs_stock():
    _require_data()
    return compute_demand_vs_stock(_analysis_context())


@router.get("/cost-efficiency")
def cost_efficiency():
    _require_data()
    return compute_cost_efficiency(_analysis_context())
