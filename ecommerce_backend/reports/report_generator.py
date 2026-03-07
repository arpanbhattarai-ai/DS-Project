"""
reports/report_generator.py  -  Generate PDF and Excel BI reports.
"""
from pathlib import Path
from logger import get_logger

from analysis.profitability  import compute_profitability
from analysis.discounts      import compute_discounts
from analysis.inventory      import compute_inventory
from analysis.products       import compute_products
from analysis.expenses       import compute_expenses
from analysis.monthly_growth import compute_monthly_growth
from analysis.breakeven      import compute_breakeven
from analysis.cashflow       import compute_cashflow

logger = get_logger(__name__)
EXPORT_DIR = Path("data/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _all(store: dict) -> dict:
    return {
        "profitability":  compute_profitability(store),
        "discounts":      compute_discounts(store),
        "inventory":      compute_inventory(store),
        "products":       compute_products(store),
        "expenses":       compute_expenses(store),
        "monthly_growth": compute_monthly_growth(store),
        "breakeven":      compute_breakeven(store),
        "cashflow":       compute_cashflow(store),
    }


def generate_pdf(store: dict) -> str:
    from fpdf import FPDF

    data = _all(store)
    p    = data["profitability"]
    be   = data["breakeven"]
    cf   = data["cashflow"]
    inv  = data["inventory"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Nepal E-Commerce BI Report 2025", ln=True, align="C")
    pdf.ln(4)

    def section(title):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "  " + title, ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 11)
        pdf.ln(2)

    def row(label, value):
        pdf.cell(95, 7, label)
        pdf.cell(0, 7, str(value), ln=True)

    section("Profitability")
    row("Gross Revenue",          f"NPR {p['gross_revenue_npr']:,.0f}")
    row("Net Revenue",            f"NPR {p['net_revenue_npr']:,.0f}")
    row("Gross Profit",           f"NPR {p['gross_profit_npr']:,.0f}  ({p['gross_profit_margin_pct']}%)")
    row("Net Profit",             f"NPR {p['net_profit_npr']:,.0f}  ({p['net_profit_margin_pct']}%)")
    row("Total Operating Expense",f"NPR {p['total_opex_npr']:,.0f}")
    pdf.ln(3)

    section("Cash Flow")
    row("Total Cash Inflow",  f"NPR {cf['total_cash_inflow_npr']:,.0f}")
    row("Total Cash Outflow", f"NPR {cf['total_cash_outflow_npr']:,.0f}")
    row("Net Cash Movement",  f"NPR {cf['net_cash_movement_npr']:,.0f}")
    pdf.ln(3)

    section("Inventory")
    row("Inventory Turnover",         f"{inv['inventory_turnover']}x")
    row("Days Inventory Outstanding", f"{inv['days_inventory_outstanding']} days")
    row("Items Below Reorder Level",  str(inv['items_below_reorder_level']))
    pdf.ln(3)

    section("Break-Even")
    row("Overall Break-Even Units", f"{be['overall_breakeven_units']:,.0f}")
    row("Actual Units Sold",        f"{be['actual_units_sold']:,.0f}")
    row("Margin of Safety",         f"{be['margin_of_safety_pct']}%")
    pdf.ln(3)

    out = str(EXPORT_DIR / "BI_Report.pdf")
    pdf.output(out)
    logger.info(f"PDF saved: {out}")
    return out


def generate_excel(store: dict) -> str:
    import pandas as pd
    data = _all(store)
    out  = str(EXPORT_DIR / "BI_Report.xlsx")

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame([data["profitability"]]).T.reset_index().rename(
            columns={"index": "Metric", 0: "Value"}
        ).to_excel(writer, sheet_name="Profitability", index=False)

        pd.DataFrame(data["monthly_growth"]["monthly"]).to_excel(
            writer, sheet_name="Monthly Growth", index=False)

        pd.DataFrame(data["products"]["top_10_products_by_revenue"]).to_excel(
            writer, sheet_name="Top Products", index=False)

        pd.DataFrame([data["expenses"]["expense_breakdown"]]).T.reset_index().rename(
            columns={"index": "Category", 0: "NPR"}
        ).to_excel(writer, sheet_name="Expenses", index=False)

        pd.DataFrame(data["cashflow"]["monthly_cashflow"]).to_excel(
            writer, sheet_name="Cash Flow", index=False)

        pd.DataFrame(data["breakeven"]["top_20_easiest_breakeven"]).to_excel(
            writer, sheet_name="Break-Even", index=False)

        pd.DataFrame(data["inventory"]["below_reorder_items"]).to_excel(
            writer, sheet_name="Reorder Alerts", index=False)

    logger.info(f"Excel saved: {out}")
    return out
