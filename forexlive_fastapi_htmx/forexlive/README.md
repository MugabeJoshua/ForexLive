# ForexLive

A standalone portfolio-ready foreign-exchange dashboard built with **FastAPI, Jinja2, HTMX, and Tailwind CSS**.

## Features
- Server-rendered initial page using FastAPI + Jinja2.
- HTMX refreshes the rates table every five minutes without reloading the page.
- HTMX-powered converter updates its result as the user types or changes currency.
- USD, EUR, GBP, KES, ZAR and JPY converted into UGX.
- Responsive dark fintech UI.
- Short server-side cache and graceful API error states.
- `/health` endpoint for deployment monitoring.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000.

## SSR and HTMX
- `GET /` fetches rates on the server and returns complete Jinja2-rendered HTML.
- `GET /partials/rates` returns only the rates-table fragment. HTMX polls this endpoint every five minutes and swaps the fragment into the page.
- `POST /convert` calculates the result server-side and returns a small HTML fragment.
- The page does not need a full reload for rate updates or conversions.

## Data source
Uses `https://open.er-api.com/v6/latest/UGX`. The provider returns units of each currency per UGX; ForexLive inverts those values to calculate UGX per one unit. Provider update timing may vary. These are indicative reference rates, not guaranteed bank, card, or forex-bureau transaction rates.

## Deployment
Deploy to a Python-compatible host such as Render or Railway. Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Set the health-check path to `/health`.

## Portfolio summary
**ForexLive** is a server-rendered foreign exchange dashboard built with FastAPI, Jinja2, HTMX, and Tailwind CSS. It fetches exchange-rate data server-side, converts six global currencies into UGX, refreshes the rates fragment without full-page reloads, and includes an interactive server-powered currency converter.
