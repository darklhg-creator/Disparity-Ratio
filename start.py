import requests

API_KEY = "62e0d95b35661ef8e1f9a665ef46cc7cd64a3ace4d179612dda40c847f6bdb7e"
url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

all_items = []
for page in range(1, 4):
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "30",
        "pageNo": str(page),
        "resultType": "json",
        "srtnCd": "156100"  # 엘앤케이바이오
    }
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    items = data['response']['body']['items']['item']
    if isinstance(items, dict):
        items = [items]
    all_items.extend(items)

# 날짜순 정렬
all_items = sorted(all_items, key=lambda x: x.get('basDt', ''))

# 최근 25일치 출력
for item in all_items[-25:]:
    print(f"날짜: {item.get('basDt')}, 종가: {item.get('clpr')}")

# MA20 직접 계산
prices = [float(str(item.get('clpr','0')).replace(',','')) for item in all_items[-20:]]
ma20 = sum(prices) / 20
current = prices[-1]
disparity = round((current / ma20) * 100, 2)
print(f"\n현재가: {current}, MA20: {round(ma20,2)}, 이격도: {disparity}%")
