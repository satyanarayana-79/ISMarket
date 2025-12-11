import requests
from bs4 import BeautifulSoup

url = "https://chartink.com/screener/best-multibagger-stocks"
scan = "({cash} ( daily high >= daily max( 260 , daily high ) * 0.9 and daily low >= daily min( 260 , daily low ) * 2 and daily close > daily sma( daily close , 100 ) and daily sma( daily close , 20 ) > daily sma( daily close , 200 ) and daily high < daily max( 260 , daily high ) * 1 and daily rsi( 14 ) >= 55 and earning per share[eps] > 20 and yearly debt equity ratio < 1 and market cap <= 5000 ) )"

payload = {"scan_clause": scan}

with requests.Session() as s:
    r = s.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    csrf = soup.select_one("meta[name='csrf-token']")["content"]

    s.headers.update({
        "X-CSRF-TOKEN": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0",
        "Referer": url,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    })

    resp = s.post("https://chartink.com/screener/process", data=payload)
    print(resp.json())
