"""
routes/report.py  -  GET /report/pdf  and  GET /report/excel
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from logger import get_logger
from reports.report_generator import generate_pdf, generate_excel
import state

router = APIRouter(prefix="/report")
logger = get_logger(__name__)


def _require_data():
    if not state.store["ready"]:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Upload a file or place an Excel file in data/raw and restart.",
        )


@router.get("/pdf")
def download_pdf():
    _require_data()
    path = generate_pdf(state.store)
    return FileResponse(path, media_type="application/pdf", filename="BI_Report.pdf")


@router.get("/excel")
def download_excel():
    _require_data()
    path = generate_excel(state.store)
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="BI_Report.xlsx",
    )
