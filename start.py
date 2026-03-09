import requests

API_KEY = "62e0d95b35661ef8e1f9a665ef46cc7cd64a3ace4d179612dda40c847f6bdb7e"

base = "https://apis.data.go.kr/1160100/service/GetKofiaStatisticsInfoService"

for endpoint in [
    "/getGrantingOfCreditBalanceInfo",
    "/getSecuritiesMarketTotalCapitalInfo"
]:
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "3",
        "pageNo": "1",
        "resultType": "json"
    }
    res = requests.get(base + endpoint, params=params, timeout=10)
    print(f"엔드포인트: {endpoint}")
    print(f"상태코드: {res.status_code}")
    print(f"응답: {res.text[:300]}")
    print()
