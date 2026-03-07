import requests

API_KEY = "62e0d95b35661ef8e1f9a665ef46cc7cd64a3ace4d179612dda40c847f6bdb7e"
url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

params = {
    "serviceKey": API_KEY,
    "numOfRows": "5",
    "pageNo": "1",
    "resultType": "json",
    "likeSrtnCd": "156100",
    "basDt": "20260306"  # 3월 6일 데이터 있는지 확인
}
res = requests.get(url, params=params, timeout=10)
data = res.json()
print("총 건수:", data['response']['body']['totalCount'])
items = data['response']['body']['items']
print("데이터:", items)
