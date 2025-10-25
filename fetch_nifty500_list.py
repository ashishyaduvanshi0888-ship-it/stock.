# fetch_nifty500_list.py
# Usage: python fetch_nifty500_list.py
import requests
import pandas as pd
import time

def fetch_nifty500_stocks(out_csv="nifty500_stocks.csv"):
    url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.nseindia.com"
    }
    session = requests.Session()
    # initial landing to get cookies
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    time.sleep(0.5)
    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])

    rows = []
    for item in data:
        symbol = item.get("symbol")
        sector = item.get("industry") or item.get("sector") or item.get("industry_type") or ""
        # NSE chart identifier typically uses SYMBOL + 'EQN'
        nse_identifier = f"{symbol}EQN"
        rows.append({"symbol": symbol, "sector": sector, "nse_identifier": nse_identifier})

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)
    print(f"✅ Saved {len(df)} NIFTY 500 rows -> {out_csv}")

if __name__ == "__main__":
    fetch_nifty500_stocks()
