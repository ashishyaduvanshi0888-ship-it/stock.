# analyze_sector_performance_nse_only.py
# NSE-only intraday analysis (09:15 - 12:15 IST)
# Usage: python analyze_sector_performance_nse_only.py --date YYYY-MM-DD
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
import time
import argparse
from tqdm import tqdm
import os

SESSION_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}

RAW_DIR = "raw_nse_minute_data"
os.makedirs(RAW_DIR, exist_ok=True)

def load_constituents(csv_file="nifty500_stocks.csv"):
    df = pd.read_csv(csv_file)
    df = df.dropna(subset=["symbol"]).drop_duplicates(subset=["symbol"]) 
    return df

def fetch_chart_data(session, identifier):
    """Fetch chart data JSON from NSE for a given identifier (e.g., RELIANCEEQN)."""
    base = "https://www.nseindia.com/api/chart-databyindex"
    params = {"index": identifier}
    try:
        r = session.get(base, params=params, timeout=10)
        if r.status_code != 200:
            return None, f"http_{r.status_code}"
        data = r.json()
        return data, None
    except Exception as e:
        return None, str(e)

def extract_price_at(data, target_dt):
    """Extract price (value) closest to target datetime from data['grapthData'].
    target_dt must be an aware datetime in IST timezone.
    Returns price (float) or None.
    """
    if not data or 'grapthData' not in data:
        return None
    points = data['grapthData']
    if not points:
        return None
    # points are [ [timestamp_ms, value], ... ] where timestamp is in UTC epoch ms
    best = None
    best_diff = None
    for ts_ms, val in points:
        # convert ms to UTC datetime then to IST
        dt_utc = datetime.fromtimestamp(ts_ms/1000.0, tz=timezone.utc)
        dt_ist = dt_utc.astimezone(tz=timezone(timedelta(hours=5, minutes=30)))
        diff = abs((dt_ist - target_dt).total_seconds())
        if best is None or diff < best_diff:
            best = val
            best_diff = diff
    # allow tolerance of 120 seconds (2 minutes)
    if best_diff is not None and best_diff <= 120:
        return float(best)
    return None

def main(date_str):
    df = load_constituents()
    session = requests.Session()
    session.headers.update(SESSION_HEADERS)
    # initial landing to get cookies
    session.get('https://www.nseindia.com', timeout=10)
    time.sleep(0.5)

    results = []
    failures = []

    # prepare target datetimes in IST
    target_0915 = datetime.strptime(f"{date_str} 09:15", "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
    target_1215 = datetime.strptime(f"{date_str} 12:15", "%Y-%m-%d %H:%M").replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))

    for _, row in tqdm(df.iterrows(), total=len(df)):
        symbol = row['symbol']
        identifier = row.get('nse_identifier') or f"{symbol}EQN"
        # some endpoints need symbol page visit first
        try:
            session.get(f'https://www.nseindia.com/get-quotes/equity?symbol={symbol}', timeout=8)
        except:
            pass
        time.sleep(0.08)  # small polite delay

        data, err = fetch_chart_data(session, identifier)
        if err:
            failures.append({'symbol': symbol, 'identifier': identifier, 'error': err})
            continue

        # save raw json for audit (if present)
        try:
            with open(os.path.join(RAW_DIR, f"{symbol}_{date_str}.json"), 'w', encoding='utf-8') as f:
                import json as _json
                _json.dump(data, f)
        except:
            pass

        price_0915 = extract_price_at(data, target_0915)
        price_1215 = extract_price_at(data, target_1215)

        if price_0915 is None or price_1215 is None:
            failures.append({'symbol': symbol, 'identifier': identifier, 'error': 'missing_prices'})
            continue

        pct_change = (price_1215 - price_0915) / price_0915 * 100
        results.append({'symbol': symbol, 'sector': row.get('sector', ''), 'price_0915': price_0915, 'price_1215': price_1215, 'pct_change': pct_change})

    res_df = pd.DataFrame(results)
    if res_df.empty:
        print('No valid data fetched. Check failures file.')
        pd.DataFrame(failures).to_csv(f'failures_{date_str}.csv', index=False)
        return

    sector_df = res_df.groupby('sector')['pct_change'].mean().reset_index().rename(columns={'pct_change':'avg_pct_change'})
    sector_df = sector_df.dropna(subset=['sector']).sort_values('avg_pct_change', ascending=False)

    top_gainers = sector_df.head(3)
    top_losers = sector_df.tail(3)

    print('\n📈 Top 3 Gaining Sectors:')
    print(top_gainers.to_string(index=False))
    print('\n📉 Top 3 Losing Sectors:')
    print(top_losers.to_string(index=False))

    # save outputs
    res_df.to_csv(f'intraday_stock_changes_{date_str}.csv', index=False)
    sector_df.to_csv(f'sector_avg_changes_{date_str}.csv', index=False)
    pd.DataFrame(failures).to_csv(f'failures_{date_str}.csv', index=False)
    print(f'\nSaved outputs: intraday_stock_changes_{date_str}.csv, sector_avg_changes_{date_str}.csv, failures_{date_str}.csv')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=None, help='Date in YYYY-MM-DD (IST). Defaults to today IST')
    args = parser.parse_args()
    if args.date:
        date_str = args.date
    else:
        # today's date IST
        from datetime import datetime, timezone, timedelta
        date_str = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d')
    print(f'Running NSE-only intraday analysis for {date_str} (09:15-12:15 IST)')
    main(date_str)
