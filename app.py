# ===================================================================
# app.py — ISMarket Date-wise, Table-wise & Recommendations Viewer
# ===================================================================

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import sqlite3
import os
import datetime
from chartink import update_all

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/")
def index():
    return "ISMarket Technical Analysis is running successfully!"
# ---------------------------------------------------------
# CORS headers (extra safety for browsers)
# ---------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ---------------------------------------------------------
# FORMAT DATE (Indian style)
# ---------------------------------------------------------
def format_indian_date():
    today = datetime.date.today()
    day = today.day

    if day in [1, 21, 31]:
        suffix = "st"
    elif day in [2, 22]:
        suffix = "nd"
    elif day in [3, 23]:
        suffix = "rd"
    else:
        suffix = "th"

    formatted_day = f"{day}{suffix}"
    month = today.strftime("%B")
    year = today.year

    return f"{formatted_day} {month} {year}"


# ---------------------------------------------------------
# TABLE → HTML Generator
# ---------------------------------------------------------
def table_to_html(rows, title):
    """
    Convert rows into an HTML table for the report.

    Even if there is no data, we still show a table
    with fixed columns:
    stock_name | price | change | volume | symbol
    """
    # Protect against None
    rows = rows or []

    # Section title
    html = f"<h3>{title}</h3>"
    html += "<table style='width:100%; border-collapse:collapse; background:#d7ecff;'>"

    # Fixed column order (same as your screenshot)
    columns = ["stock_name", "price", "change", "volume", "symbol"]

    # ---- Header row ----
    html += "<tr>"
    for col in columns:
        html += f"<th style='border:1px solid #000; padding:6px;'>{col}</th>"
    html += "</tr>"

    # ---- Data rows (only if we have any) ----
    for row in rows:
        html += "<tr>"
        for col in columns:
            value = row.get(col, "")
            html += f"<td style='border:1px solid #000; padding:6px;'>{value}</td>"
        html += "</tr>"

    html += "</table><br>"
    return html



def filter_top5_for_report(rows):
    """
    Apply all business rules for Technical Analysis Report:

    1) Only top 5 stocks (by % change, highest first)
    2) Skip if % change < 2
    3) Skip if volume < 2000
    4) Skip if price < 5
    5) Skip dummy 'N/A' rows
    """
    filtered = []

    for r in rows:
        # Skip dummy / empty rows
        name = str(r.get("stock_name", "")).strip()
        if not name or name.upper() == "N/A":
            continue

        # Safely convert values
        try:
            price = float(r.get("price") or 0)
        except Exception:
            price = 0.0

        try:
            change = float(r.get("change") or 0)
        except Exception:
            change = 0.0

        try:
            volume = int(r.get("volume") or 0)
        except Exception:
            volume = 0

        # Apply your conditions
        if change < 2:      # condition 2
            continue
        if volume < 2000:   # condition 3
            continue
        if price < 5:       # condition 4
            continue

        filtered.append(r)

    # Sort by % change (highest first) and take only top 5
    filtered.sort(key=lambda x: float(x.get("change") or 0), reverse=True)
    return filtered[:5]

# ---------------------------------------------------------
# PATH SETTINGS
# ---------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MAIN_DB = os.path.join(BASE_DIR, "chartink_data.db")

TABLES = {
    "bms": "Best Multibagger Stocks",
    "lowest_pe": "Lowest PE Stocks",
    "bullish_script": "Bullish Script",
    "profit_jump": "Profit Jump",
    "sales_jump": "Sales Jump",
    "below_book_value": "Below Book Value",
    "buy_entry_intraday": "Buy Entry Intraday",

    # NEW PATTERN SCREENS
    "short_term_breakouts": "Short Term Breakouts",
    "potential_breakouts": "Potential Breakouts",
    "bearish_engulf_5m": "Bearish Engulfing (5m)",
    "tweezer_bottom_15m": "Tweezer Bottom (15m)",
    "bullish_harami_15m": "Bullish Harami (15m)",
    "dragonfly_doji_15m": "Dragonfly Doji (15m)",
    "bearish_kicker_15m": "Bearish Kicker Pattern (15m)",
    "first_15m_breakout_both": "First 15-min Candle Breakout (Both Sides)",
    "morning_star_bullish": "Morning Star Bullish Pattern",
    "bearish_engulfing_strong": "Bearish Engulfing – Strong",
}

# ---------------------------------------------------------
# FORMULAS (Chartink-style HTML snippets)
# ---------------------------------------------------------
FORMULAS = {
    "bms": """
      <div class="formula-title">Best Multibagger Stocks</div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&lt;</span> <span class="f-num">30</span></div>
      <div class="formula-line"><span class="f-key">Daily EMA20</span> <span class="f-op">&gt;</span> <span class="f-key">Daily EMA50</span></div>
      <div class="formula-line"><span class="f-key">Price Change %</span> <span class="f-op">&gt;</span> <span class="f-num">0</span></div>
    """,

    "lowest_pe": """
      <div class="formula-title">Lowest PE Stocks (RSI Proxy)</div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&lt;</span> <span class="f-num">40</span></div>
      <div class="formula-line"><span class="f-key">Price</span> <span class="f-op">near</span> <span class="f-key">52-week Low (proxy)</span></div>
    """,

    "bullish_script": """
      <div class="formula-title">Bullish Script</div>
      <div class="formula-line"><span class="f-key">Daily EMA20</span> <span class="f-op">&gt;</span> <span class="f-key">Daily EMA50</span></div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&gt;</span> <span class="f-num">55</span></div>
    """,

    "profit_jump": """
      <div class="formula-title">Profit Jump</div>
      <div class="formula-line"><span class="f-key">Daily % Change</span> <span class="f-op">&gt;</span> <span class="f-num">2%</span></div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&gt;</span> <span class="f-num">50</span></div>
    """,

    "sales_jump": """
      <div class="formula-title">Sales Jump (Weak Day)</div>
      <div class="formula-line"><span class="f-key">Daily % Change</span> <span class="f-op">&lt;</span> <span class="f-num">-1%</span></div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&lt;</span> <span class="f-num">45</span></div>
    """,

    "below_book_value": """
      <div class="formula-title">Below Book Value (Proxy)</div>
      <div class="formula-line"><span class="f-key">Price</span> <span class="f-op">&lt;</span> <span class="f-num">₹200</span></div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">&lt;</span> <span class="f-num">35</span></div>
    """,

    "buy_entry_intraday": """
      <div class="formula-title">Buy Entry Intraday</div>
      <div class="formula-line"><span class="f-key">Daily EMA20</span> <span class="f-op">&gt;</span> <span class="f-key">Daily EMA50</span></div>
      <div class="formula-line"><span class="f-key">Daily RSI(14)</span> <span class="f-op">between</span> <span class="f-num">45</span> <span class="f-op">and</span> <span class="f-num">60</span></div>
    """,

    "short_term_breakouts": """
      <div class="formula-title">Short Term Breakouts</div>
      <div class="formula-line">
        <span class="f-key">Daily High</span> <span class="f-op">&gt;=</span>
        <span class="f-func">Max(260, Daily High)</span> <span class="f-op">×</span> <span class="f-num">0.9</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Market Cap</span> <span class="f-op">&lt;=</span> <span class="f-num">5000</span> <span class="f-unit">Cr</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Daily Low</span> <span class="f-op">&gt;=</span>
        <span class="f-func">Min(260, Daily Low)</span> <span class="f-op">×</span> <span class="f-num">2</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Daily Close</span> <span class="f-op">&gt;</span>
        <span class="f-func">SMA( Daily Close , 100 )</span>
      </div>
      <div class="formula-line">
        <span class="f-func">SMA( Daily Close , 20 )</span>
        <span class="f-op">&gt;</span>
        <span class="f-func">SMA( Daily Close , 200 )</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Daily High</span> <span class="f-op">&lt;</span>
        <span class="f-func">Max(260, Daily High)</span> <span class="f-op">×</span> <span class="f-num">1.0</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Daily RSI(14)</span> <span class="f-op">&gt;=</span> <span class="f-num">55</span>
      </div>
      <div class="formula-line">
        <span class="f-key">EPS</span> <span class="f-op">&gt;</span> <span class="f-num">20</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Yearly Debt/Equity</span> <span class="f-op">&lt;</span> <span class="f-num">1</span>
      </div>
    """,

    "potential_breakouts": """
      <div class="formula-title">Potential Breakouts</div>
      <div class="formula-line"><span class="f-key">Daily EMA20</span> <span class="f-op">&gt;</span> <span class="f-key">Daily EMA50</span></div>
      <div class="formula-line"><span class="f-key">Daily Close</span> <span class="f-op">within</span> <span class="f-num">2%</span> <span class="f-op">of</span> <span class="f-func">Max(60, Close)</span></div>
      <div class="formula-line"><span class="f-key">Daily Volume</span> <span class="f-op">&gt;</span> <span class="f-func">SMA(Volume , 10)</span></div>
    """,

    "bearish_engulf_5m": """
      <div class="formula-title">Bearish Engulfing after Downtrend (5m Proxy)</div>
      <div class="formula-line"><span class="f-key">Prev Trend</span> <span class="f-op">8 candles</span> <span class="f-op">down</span></div>
      <div class="formula-line"><span class="f-key">Current 5m Candle</span> <span class="f-op">red</span> <span class="f-op">engulfing</span> <span class="f-key">previous 5m green</span></div>
      <div class="formula-line"><span class="f-key">RSI(14)</span> <span class="f-op">&gt;</span> <span class="f-num">55</span> <span class="f-op">(reversal zone)</span></div>
    """,

    "tweezer_bottom_15m": """
      <div class="formula-title">Tweezer Bottom (15m Proxy)</div>
      <div class="formula-line"><span class="f-key">Two candles</span> <span class="f-op">with</span> <span class="f-key">same Low</span></div>
      <div class="formula-line"><span class="f-key">First candle</span> <span class="f-op">red</span>, <span class="f-key">second</span> <span class="f-op">green</span></div>
      <div class="formula-line"><span class="f-key">RSI(14)</span> <span class="f-op">&lt;</span> <span class="f-num">40</span></div>
    """,

    "bullish_harami_15m": """
      <div class="formula-title">Bullish Harami (15m Proxy)</div>
      <div class="formula-line"><span class="f-key">Prev 15m candle</span> <span class="f-op">large red</span></div>
      <div class="formula-line"><span class="f-key">Current 15m candle</span> <span class="f-op">small green</span> <span class="f-op">inside body</span> <span class="f-key">of previous</span></div>
      <div class="formula-line"><span class="f-key">RSI(14)</span> <span class="f-op">rising above</span> <span class="f-num">40</span></div>
    """,

    "dragonfly_doji_15m": """
      <div class="formula-title">Dragonfly Doji (15m Proxy)</div>
      <div class="formula-line"><span class="f-key">Open ≈ Close</span> <span class="f-op">(body very small)</span></div>
      <div class="formula-line"><span class="f-key">Long lower shadow</span>, <span class="f-key">almost no upper</span></div>
      <div class="formula-line"><span class="f-key">Occurs after</span> <span class="f-op">down move</span></div>
    """,

    "bearish_kicker_15m": """
      <div class="formula-title">Bearish Kicker Pattern (15m Proxy)</div>
      <div class="formula-line"><span class="f-key">Gap-down open</span> <span class="f-op">below</span> <span class="f-key">previous green close</span></div>
      <div class="formula-line"><span class="f-key">Current candle</span> <span class="f-op">strong red</span></div>
      <div class="formula-line"><span class="f-key">Previous trend</span> <span class="f-op">up</span> <span class="f-op">(high RSI)</span></div>
    """,

    "first_15m_breakout_both": """
      <div class="formula-title">First 15-min Candle Breakout (Both Sides)</div>
      <div class="formula-line">
        <span class="f-key">Timeframe</span> <span class="f-op">=</span> <span class="f-num">15 min</span>
      </div>
      <div class="formula-line">
        <span class="f-key">LTP</span> <span class="f-op">&gt;</span>
        <span class="f-key">High</span> <span class="f-op">of first 15m candle</span>
      </div>
      <div class="formula-line">
        <span class="f-op">OR</span>
      </div>
      <div class="formula-line">
        <span class="f-key">LTP</span> <span class="f-op">&lt;</span>
        <span class="f-key">Low</span> <span class="f-op">of first 15m candle</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Intraday Volume</span> <span class="f-op">&gt;</span>
        <span class="f-func">SMA( Volume , 5 )</span>
      </div>
    """,

    "morning_star_bullish": """
      <div class="formula-title">Morning Star Bullish Pattern</div>
      <div class="formula-line">
        <span class="f-key">Candle 1</span> <span class="f-op">=</span>
        <span class="f-text">long red body, closing near low</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Candle 2</span> <span class="f-op">=</span>
        <span class="f-text">small body (gap-down) showing indecision</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Candle 3</span> <span class="f-op">=</span>
        <span class="f-text">strong green closing into / above mid of Candle&nbsp;1 body</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Recent trend</span> <span class="f-op">=</span>
        <span class="f-text">down move before pattern</span>
      </div>
    """,

    "bearish_engulfing_strong": """
      <div class="formula-title">Bearish Engulfing – Strong</div>
      <div class="formula-line">
        <span class="f-key">Prev candle</span> <span class="f-op">=</span>
        <span class="f-text">green body after short-term uptrend</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Current candle</span> <span class="f-op">=</span>
        <span class="f-text">large red body engulfing previous body high–low</span>
      </div>
      <div class="formula-line">
        <span class="f-key">Body size</span> <span class="f-op">&gt;</span>
        <span class="f-num">1.5×</span> <span class="f-text">average of last 5 candles</span>
      </div>
      <div class="formula-line">
        <span class="f-key">RSI(14)</span> <span class="f-op">&gt;</span> <span class="f-num">55</span>
        <span class="f-text">(overbought / reversal zone)</span>
      </div>
    """,
}

# ---------------------------------------------------------
# GET DB PATH FOR SPECIFIC DAY OR LATEST
# ---------------------------------------------------------
def get_db_path_for_day(day=None):
    daily_dir = os.path.join(BASE_DIR, "daily_dbs")

    if not os.path.exists(daily_dir):
        return None

    if day:
        db_file = os.path.join(daily_dir, f"{day}.db")
        return db_file if os.path.exists(db_file) else None

    files = [f for f in os.listdir(daily_dir) if f.endswith(".db")]
    if not files:
        return None
    latest = sorted(files, reverse=True)[0]
    return os.path.join(daily_dir, latest)


# ---------------------------------------------------------
def read_table_from_daily_db(db_path, table_name):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(f'SELECT * FROM "{table_name}"').fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", titles=TABLES)


@app.route("/api/get_days")
def get_days():
    daily_dir = os.path.join(BASE_DIR, "daily_dbs")
    if not os.path.exists(daily_dir):
        return jsonify({"days": []})
    days = [f.replace(".db", "") for f in os.listdir(daily_dir) if f.endswith(".db")]
    days.sort(reverse=True)
    return jsonify({"days": days})


# ---------------------------------------------------------
# API — TODAY TECHNICAL REPORT (Sections 1–7)
# ---------------------------------------------------------
@app.route("/api/today-report")
def today_report():
    today_str = format_indian_date()
    db_path = get_db_path_for_day(None)

    if not db_path:
        return jsonify({
            "title": f"Technical Analysis Report — {today_str}",
            "summary": "No database found for today.",
            "content": "<p>No data available. Please run update first.</p>"
        })

    # Sections included in the report (you can add more later)
    section_keys = [
        ("bms", "Best Multibagger Stocks"),
        ("lowest_pe", "Top stocks with the lowest Price Earning Ratios(PE)"),
        ("bullish_script", "Bullish Script"),
        ("profit_jump", "Profit jump by 200%"),
        ("sales_jump", "Sales jump by 200%"),
        ("below_book_value", "Stocks below Book value - Undervalued"),
        ("buy_entry_intraday", "Buy entry intraday"),
    ]

    # Report header
    full_html = f"""
        <h2>Technical Analysis Report — {today_str}</h2>
        <p>This report is automatically generated from Chartink screeners.</p>
        <br>
    """

    # Build each section with filters applied
    for i, (key, title) in enumerate(section_keys, start=1):
        rows = read_table_from_daily_db(db_path, key)

        # ✅ apply your conditions and take top 5
        rows_filtered = filter_top5_for_report(rows)

        full_html += table_to_html(rows_filtered, f"{i}.) {title}")

    return jsonify({
        "title": f"Technical Analysis Report — {today_str}",
        "summary": f"Technical analysis report as on {today_str}.",
        "content": full_html
    })



@app.route("/api/get_table/<table>")
def get_table(table):
    day = request.args.get("day")
    if day:
        day = day.replace("-", "_")
    db_path = get_db_path_for_day(day)
    if not db_path:
        return jsonify({"error": "DB not found", "day": day}), 500

    data = {}
    if table == "all":
        for t in TABLES.keys():
            data[t] = read_table_from_daily_db(db_path, t)
    elif table in TABLES:
        data[table] = read_table_from_daily_db(db_path, table)
    else:
        return jsonify({"error": "Invalid table"}), 400

    return jsonify({"day": day, "tables": data})


@app.route("/api/update_live")
def update_live():
    try:
        update_all()
        return jsonify({"status": "ok", "message": "Live data updated successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------
# HTML VIEWS
# ---------------------------------------------------------
@app.route("/view/all")
def view_all():
    day = request.args.get("day")
    if day:
        day = day.replace("-", "_")
    db_path = get_db_path_for_day(day)

    tables_data = {}
    if db_path:
        for key in TABLES:
            tables_data[key] = read_table_from_daily_db(db_path, key)

    return render_template(
        "view.html",
        title="All Recommendations",
        tables=tables_data,
        titles=TABLES,
        day=day,
        current_table=None,
        formulas=FORMULAS,
    )


@app.route("/view/<table>")
def view_single_table(table):
    day = request.args.get("day")
    if day:
        day = day.replace("-", "_")
    db_path = get_db_path_for_day(day)

    tables_data = {}
    if db_path and table in TABLES:
        tables_data[table] = read_table_from_daily_db(db_path, table)

    return render_template(
        "view.html",
        title=TABLES.get(table, "Unknown Screener"),
        tables=tables_data,
        titles=TABLES,
        day=day,
        current_table=table,
        formulas=FORMULAS,
    )


# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 ISMarket running → http://127.0.0.1:8000")
    print("📘 Using DB folder:", os.path.join(BASE_DIR, "daily_dbs"))
    app.run(host="0.0.0.0", port=8000, debug=True)

