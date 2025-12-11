import os
import sqlite3
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ===================================================================
# PATHS & SETTINGS
# ===================================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DB_FOLDER = os.path.join(BASE_DIR, "daily_dbs")
MAIN_DB = os.path.join(BASE_DIR, "chartink_data.db")
os.makedirs(DB_FOLDER, exist_ok=True)

TODAY_KEY = datetime.now().strftime("%Y_%m_%d")
DAILY_DB = os.path.join(DB_FOLDER, f"{TODAY_KEY}.db")

FINAL_COLS = ["stock_name", "price", "change", "volume", "symbol"]



# ===================================================================
# CHARTINK SCANS + LINKS
#   - For now only bms has real scan code
#   - Others will use fallback until you fill their scan clauses
# ===================================================================

CHARTINK_SCANS = {
    "bms": {
        "url": "https://chartink.com/screener/best-multibagger-stocks",
        # Your scan clause text (spaces are fine)
        "scan": "({cash} ( daily high >= daily max( 260 , daily high ) * 0.9 and daily low >= daily min( 260 , daily low ) * 2 and daily close > daily sma( daily close , 100 ) and daily sma( daily close , 20 ) > daily sma( daily close , 200 ) and daily high < daily max( 260 , daily high ) * 1 and daily rsi( 14 ) >= 55 and earning per share[eps] > 20 and yearly debt equity ratio < 1 and market cap <= 5000 ) )",
    },

    "lowest_pe": {
        "url": "https://chartink.com/screener/top-stocks-with-the-lowest-pe-pricing-earnings",
        "scan": "( {cash} ( market cap / yearly net profit after minority interest & pnl assoco < 5 and market cap / yearly net profit after minority interest & pnl assoco >= 1 ) ) ",
    },
    "bullish_script": {
        "url": "https://chartink.com/screener/copy-bullish-script-165",
        "scan": "( {cash} ( daily close > daily sma( close,200 ) and daily close > daily ema( close,200 ) and daily close > weekly sma( close,200 ) and daily close > weekly ema( close,200 ) and daily close > monthly sma( close,200 ) and daily rsi( 14 ) > 51 and weekly rsi( 14 ) > 51 and monthly rsi( 14 ) > 51 and daily macd histogram( 26,12,9 ) > 0 and weekly macd histogram( 26,12,9 ) > 0 and monthly macd histogram( 26,12,9 ) > 0 and daily close > ( 200 days ago high ) and daily volume >= 200000 ) ) ",
    },
    "profit_jump": {
        "url": "https://chartink.com/screener/profit-jump-by-200",
        "scan": "( {cash} ( net profit[yearly] > ttm net profit * 2 and net profit[yearly] > 0 and ttm net profit > 0 ) ) ",
    },
    "sales_jump": {
        "url": "https://chartink.com/screener/sales-jump-by-200",
        "scan": "( {cash} ( sales turnover[yearly] > ttm sales * 2 ) ) ",
    },
    "below_book_value": {
        "url": "https://chartink.com/screener/stocks-below-book-value",
        "scan": "( {cash} ( daily close < yearly book value ) ) ",
    },
    "buy_entry_intraday": {
        "url": "https://chartink.com/screener/buy-entry-intraday",
        "scan": "( {33489} ( daily parabolic sar( 0.04,0.02,0.2 ) < daily ema( close,9 ) and 1 day ago  parabolic sar( 0.04,0.02,0.2 ) >= 1 day ago  ema( close,9 ) ) ) ",
    },

    # These still don’t have scan codes → will fallback to N/A until you add
    "short_term_breakouts": {"url": "https://chartink.com/screener/", "scan": None},
    "potential_breakouts": {"url": "https://chartink.com/screener/", "scan": None},
    "bearish_engulf_5m": {"url": "https://chartink.com/screener/", "scan": None},
    "tweezer_bottom_15m": {"url": "https://chartink.com/screener/", "scan": None},
    "bullish_harami_15m": {"url": "https://chartink.com/screener/", "scan": None},
    "dragonfly_doji_15m": {"url": "https://chartink.com/screener/", "scan": None},
    "bearish_kicker_15m": {"url": "https://chartink.com/screener/", "scan": None},
    "first_15m_breakout_both": {"url": "https://chartink.com/screener/", "scan": None},
    "morning_star_bullish": {"url": "https://chartink.com/screener/", "scan": None},
    "bearish_engulfing_strong": {"url": "https://chartink.com/screener/", "scan": None},
}

# ===================================================================
# FALLBACK DF
# ===================================================================

def fallback_df():
    return pd.DataFrame(
        [{
            "stock_name": "N/A",
            "symbol": "N/A",
            "open": 0,
            "high": 0,
            "low": 0,
            "close": 0,
            "ltp": 0,
            "change_percent": 0,
            "volume": 0,
            "delivery_percent": 0,
            "trades": 0,
            "value": 0,
        }],
        columns=FINAL_COLS,
    )


# ===================================================================
# Chartink fetch using csrf-token from <meta> tag
# ===================================================================

def get_chartink_results(key, cfg):
    scan_code = cfg.get("scan")
    screener_url = cfg.get("url") or "https://chartink.com/screener/"

    if not scan_code:
        print(f"⚠ No scan code for {key} → fallback")
        return fallback_df()

    print(f"\n🔎 Fetching screener → {key}")

    payload = {"scan_clause": scan_code}

    try:
        with requests.Session() as s:
            # Fetch CSRF token
            r = s.get(screener_url, timeout=15)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            csrf_tag = soup.select_one("meta[name='csrf-token']")
            if not csrf_tag:
                print("❌ CSRF not found → fallback")
                return fallback_df()

            csrf = csrf_tag["content"]

            s.headers.update({
                "X-CSRF-TOKEN": csrf,
                "User-Agent": "Mozilla/5.0",
                "Referer": screener_url,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            })

            resp = s.post("https://chartink.com/screener/process",
                          data=payload, timeout=15)
            resp.raise_for_status()

            data_json = resp.json()

    except Exception as e:
        print(f"❌ ERROR → {e}")
        return fallback_df()

    rows_json = data_json.get("data", [])
    if not rows_json:
        print(f"⚠ Chartink returned 0 rows for {key}")
        return fallback_df()

    # Correct mapping
    rows = []
    for r in rows_json:
        rows.append({
            "stock_name": r.get("name", ""),
            "price": r.get("close", 0),
            "change": r.get("per_chg", 0),
            "volume": r.get("volume", 0),
            "symbol": r.get("nsecode", "")
        })

    df = pd.DataFrame(rows, columns=FINAL_COLS)

    # ⭐ FILTER: change >= 2
    df = df[df["change"] >= 2]

    # ⭐ SORT: highest change first
    df = df.sort_values(by="change", ascending=False)

    # ⭐ LIMIT: top 5 rows
    df = df.head(5)

    # Fallback if nothing remains
    if df.empty:
        print(f"⚠ After filtering top 5 change>=2 → nothing for {key}")
        return fallback_df()

    return df




   


# ===================================================================
# Build ALL screeners
# ===================================================================

def build_screeners():
    screeners = {}
    for key, cfg in CHARTINK_SCANS.items():
        screeners[key] = get_chartink_results(key, cfg)
    return screeners

# ===================================================================
# Save DB
# ===================================================================

def save_daily_db(screeners):
    conn = sqlite3.connect(DAILY_DB)
    for name, df in screeners.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"💾 Saved Daily DB → {DAILY_DB}")
    return DAILY_DB


def register_daily_db(path):
    conn = sqlite3.connect(MAIN_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            day TEXT PRIMARY KEY,
            db_path TEXT
        )
        """
    )
    conn.execute("REPLACE INTO records VALUES (?, ?)", (TODAY_KEY, path))
    conn.commit()
    conn.close()
    print("📘 Updated main DB index")

# ===================================================================
# Main Function
# ===================================================================

def update_all():
    print("\n🚀 Updating ALL Screeners using Chartink...\n")

    screeners = build_screeners()
    dbpath = save_daily_db(screeners)
    register_daily_db(dbpath)

    print("\n🎯 Screener Update Completed Successfully!\n")
    return True


if __name__ == "__main__":
    update_all()
