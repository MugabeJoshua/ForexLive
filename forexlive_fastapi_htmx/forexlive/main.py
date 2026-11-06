from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ForexLive", description="Server-rendered UGX exchange-rate dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

PROVIDER_URL = "https://open.er-api.com/v6/latest/UGX"
CACHE_SECONDS = 300
CURRENCIES = [
    {"code": "USD", "name": "US Dollar", "flag": "🇺🇸"},
    {"code": "EUR", "name": "Euro", "flag": "🇪🇺"},
    {"code": "GBP", "name": "British Pound", "flag": "🇬🇧"},
    {"code": "KES", "name": "Kenyan Shilling", "flag": "🇰🇪"},
    {"code": "ZAR", "name": "South African Rand", "flag": "🇿🇦"},
    {"code": "JPY", "name": "Japanese Yen", "flag": "🇯🇵"},
]
_rate_cache = {"expires": 0.0, "data": None}


def format_rate(value: Optional[float]) -> str:
    if value is None:
        return "Unavailable"
    return f"{value:,.{4 if value < 100 else 2}f}"


async def get_rates(force_refresh: bool = False) -> dict:
    now = datetime.now(timezone.utc).timestamp()
    if not force_refresh and _rate_cache["data"] and now < _rate_cache["expires"]:
        return _rate_cache["data"]

    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.get(PROVIDER_URL, headers={"Accept": "application/json"})
        response.raise_for_status()
        payload = response.json()

    if payload.get("result") != "success" or not isinstance(payload.get("rates"), dict):
        raise RuntimeError("Invalid exchange-rate provider response.")

    provider_rates = payload["rates"]
    rows = []
    for currency in CURRENCIES:
        units_per_ugx = provider_rates.get(currency["code"])
        ugx = (1 / float(units_per_ugx)) if units_per_ugx else None
        rows.append({**currency, "ugx": ugx, "formatted": format_rate(ugx)})

    data = {
        "rates": rows,
        "updated_at": payload.get("time_last_update_utc", "Timestamp unavailable"),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    _rate_cache["data"] = data
    _rate_cache["expires"] = now + CACHE_SECONDS
    return data


def render(request: Request, template: str, **context):
    return templates.TemplateResponse(request=request, name=template, context=context)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        data, error = await get_rates(), None
    except (httpx.HTTPError, RuntimeError, ValueError):
        data, error = _rate_cache["data"], "Live rates are temporarily unavailable. Please try again shortly."
    return render(request, "index.html", data=data, error=error)


@app.get("/partials/rates", response_class=HTMLResponse)
async def rates_partial(request: Request):
    try:
        data, error = await get_rates(), None
    except (httpx.HTTPError, RuntimeError, ValueError):
        data, error = _rate_cache["data"], "Could not refresh rates. Showing the last available values."
    return render(request, "partials/rates.html", data=data, error=error)


@app.post("/convert", response_class=HTMLResponse)
async def convert(request: Request, amount: str = Form("1"), currency: str = Form("USD")):
    try:
        numeric_amount = float(amount)
        if numeric_amount < 0 or numeric_amount > 1_000_000_000:
            raise ValueError
    except ValueError:
        return render(request, "partials/conversion_result.html", result=None, message="Enter a valid amount.")

    try:
        data = await get_rates()
    except (httpx.HTTPError, RuntimeError, ValueError):
        data = _rate_cache["data"]

    selected = next((item for item in (data or {}).get("rates", []) if item["code"] == currency), None)
    if not selected or selected["ugx"] is None:
        return render(request, "partials/conversion_result.html", result=None,
                      message="That currency rate is currently unavailable.")

    result = numeric_amount * selected["ugx"]
    return render(request, "partials/conversion_result.html", result=f"{result:,.2f}",
                  message=f"{numeric_amount:,.4g} {currency} converted using the displayed reference rate.")


@app.get("/health")
async def health():
    return {"status": "ok", "app": "ForexLive"}
