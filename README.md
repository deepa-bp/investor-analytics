# Investor Lifecycle Analytics (Millburn prototype)

A single-page analytics dashboard that follows individual investors from first website visit to full redemption, split by acquisition source (website, referral, RIA advisers, broker-dealer agents, alt platforms).

**All data in `data/` is sample data generated for the prototype. None of it is Millburn's.**

## Run it

The page loads CSV files with `fetch`, so it needs a local web server (opening `index.html` directly from disk will not load the data).

```bash
cd millburn-investor-analytics
python3 -m http.server 8000
# open http://localhost:8000
```

Needs an internet connection the first time to load d3 v7 from cdnjs.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The dashboard: markup, styles, calculations (`dash.calc`) and chart code (d3 v7). |
| `dash-shim.js` | Local stand-in for the dashboard runtime: loads the datasets, runs the calculations, holds filter state. Edit `DATASETS` to point at real endpoints. |
| `theme.css` | Colour, spacing and type tokens the page uses, with light and dark themes. |
| `data/sample_*.csv` | Sample datasets (investors, journey events, monthly flows, monthly funnel). |
| `scripts/generate_sample_data.py` | Regenerates the sample CSVs (`python3 scripts/generate_sample_data.py` from the project root). Fixed seed, so output is repeatable. |

## Data model

| Dataset | Grain | Production source |
| --- | --- | --- |
| `investors` | One row per investor or prospect: source, introducing firm, stage, funding date, amounts, redemption, warning sign | CRM + platform's person record + fund administrator |
| `events` | One row per journey step: visit, registration, verification, meeting/proposal, subscription, funding, top-up, redemption | Platform's append-only event log |
| `flows` | Month × source: new investors, subscriptions, top-ups, redemptions, active investors, month-end assets | Fund administrator (capital activity, NAV) |
| `funnel` | Month × source × stage: people reaching each stage | Web analytics + platform event log |

Derived figures (headline KPIs, funnel totals, stage conversion, retention cohorts, redemption reasons, stage counts) are computed in the browser by the `dash.calc` blocks at the top of `index.html`'s script. In production these are better moved into SQL views or the API.

## Moving to production

1. Replace the CSV paths in `dash-shim.js` with API endpoints returning the same columns (JSON arrays of row objects work if you swap `d3.csvParse` for `res.json()`).
2. Move the `dash.calc` logic into the back end so numbers match other reports.
3. Add authentication: the investor table and journey view contain personal financial data.
4. Hard-coded window: "last 12 months" is Oct 2025 – Sep 2026 (`'2025-10'` cut-off and `'2026-09'` month-end in the calculations). Make it relative to today or a date filter.
