import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

# KOFIA 고객예탁금/신용잔고
url = "https://www.kofia.or.kr/brd/m_215/view.do"
res = requests.get(url, headers=headers, timeout=10)
print("상태코드:", res.status_code)
print("응답:", res.text[:300])
