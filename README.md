# NIFTY500 Sector Analysis — NSE-only Version (Intraday 09:15-12:15 IST)

**Author:** Ashish Yadav

## Overview
This repository implements the Indian Stock Market Machine Coding Challenge with **NSE website as the only data source**. 
It fetches the NIFTY 500 constituents and minute-level intraday prices directly from NSE's public JSON endpoints and computes the top 3 gaining and top 3 losing sectors between 09:15 and 12:15 IST for a given trading day.

## Files
- `fetch_nifty500_list.py` — Scrapes NIFTY 500 constituents from NSE and saves `nifty500_stocks.csv`.
- `analyze_sector_performance_nse_only.py` — Fetches minute data from NSE (`/api/chart-databyindex`) and computes sector averages.
- `requirements.txt` — Python dependencies.
- `sample_output/` — Example output CSVs.
- `raw_nse_minute_data/` — (created by running scripts) raw JSON per symbol for auditing.

## How to run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Fetch constituents:
   ```bash
   python fetch_nifty500_list.py
   ```

3. Run NSE-only analysis (for a specific date):
   ```bash
   python analyze_sector_performance_nse_only.py --date 2025-10-24
   ```
   If `--date` is omitted, it uses today's date in IST.

## Outputs
- `intraday_stock_changes_<date>.csv` — per-stock prices and % change between 09:15 and 12:15 IST.
- `sector_avg_changes_<date>.csv` — average % change per sector.
- `failures_<date>.csv` — symbols with missing data or request errors.
- `raw_nse_minute_data/` — raw JSON files fetched from NSE for auditing.

## Notes & Caveats
- NSE's chart endpoint (`/api/chart-databyindex`) provides minute-level data only for the current day and may return limited historical coverage. The script reads the grapthData array and finds the closest timestamps to 09:15 and 12:15 IST (2-minute tolerance).
- Be polite to NSE servers: the script includes short delays and uses a session with browser-like headers. If you run it for all 500 symbols, it may take several minutes; reduce concurrency to be safe.
- If NSE changes their APIs, minor changes to the request/identifier format may be required.
- This implementation uses the NSE endpoints directly to satisfy the strict "NSE-only" requirement.

## Author
Ashish Yadav
