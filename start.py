import requests

API_KEY = "62e0d95b35661ef8e1f9a665ef46cc7cd64a3ace4d179612dda40c847f6bdb7e"

url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
params = {
    "serviceKey": API_KEY,
    "numOfRows": "5",
    "pageNo": "1",
    "resultType": "json",
    "basDt": "20260305"  # 가장 최근 거래일 금요일
}

res = requests.get(url, params=params, timeout=10)
data = res.json()
items = data['response']['body']['items']['item']

for item in items:
    print(f"종목: {item.get('itmsNm')}, EPS: {item.get('eps')}, 필드목록: {list(item.keys())}")
