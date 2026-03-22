from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings


@dataclass(frozen=True)
class EndpointSpec:
    key: str
    path: str


ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec("profitability", "/analysis/profitability"),
    EndpointSpec("discounts", "/analysis/discounts"),
    EndpointSpec("inventory", "/analysis/inventory"),
    EndpointSpec("products", "/analysis/products"),
    EndpointSpec("expenses", "/analysis/expenses"),
    EndpointSpec("monthly_growth", "/analysis/monthly-growth"),
    EndpointSpec("breakeven", "/analysis/breakeven"),
    EndpointSpec("cashflow", "/analysis/cashflow"),
)


def _fetch_json(path: str, period: str, bucket: str | None = None) -> dict[str, Any]:
    url = f"{settings.FASTAPI_BASE_URL.rstrip('/')}{path}"
    params = {"period": period}
    if bucket:
        params["bucket"] = bucket

    response = requests.get(
        url,
        params=params,
        timeout=settings.DASHBOARD_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def fetch_dashboard_payload(period: str = "monthly", bucket: str | None = None) -> tuple[dict[str, Any], list[str]]:
    payload: dict[str, Any] = {}
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=len(ENDPOINTS)) as pool:
        future_map = {
            pool.submit(_fetch_json, endpoint.path, period, bucket): endpoint
            for endpoint in ENDPOINTS
        }
        for future in as_completed(future_map):
            endpoint = future_map[future]
            try:
                payload[endpoint.key] = future.result()
            except Exception as exc:  # noqa: BLE001 - keep dashboard resilient to partial failure.
                payload[endpoint.key] = {}
                errors.append(f"{endpoint.path}: {exc}")

    return payload, errors
