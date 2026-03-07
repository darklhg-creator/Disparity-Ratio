import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# ==========================================
# 0. 사용자 설정
# ==========================================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1461902939139604684/ZdCdITanTb3sotd8LlCYlJzSYkVLduAsjC6CD2h26X56wXoQRw7NY72kTNzxTI6UE4Pi"
API_KEY = "62e0d95b35661ef8e1f9a665ef46cc7cd64a3ace4d179612dda40c847f6bdb7e"

KST_TIMEZONE = timezone(timedelta(hours=9))
CURRENT_KST = datetime.now(KST_TIMEZONE)
TARGET_DATE = CURRENT_KST.strftime("%Y-%m-%d")

# ==========================================
# 1. 공통 함수
# ==========================================
def send_discord_message(content):
    try:
        data = {'content': content}
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

# ==========================================
# 2. 공공데이터포털 API로 주식 시세 가져오기
# ==========================================
def get_stock_price(code):
    url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "30",
        "pageNo": "1",
        "resultType": "json",
        "likeSrtnCd": code
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data['response']['body']['items']['item']
        if isinstance(items, dict):
            items = [items]
        df = pd.DataFrame(items)
        df['clpr'] = pd.to_numeric(df['clpr'].str.replace(',', ''), errors='coerce')
        df = df.sort_values('basDt')
        return df
    except:
        return None

# ==========================================
# 3. 종목 리스트 가져오기
# ==========================================
def get_stock_list():
    print("📡 종목 리스트 불러오는 중...")
    url = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
    
    rows = []
    for market in ["KOSPI", "KOSDAQ"]:
        page = 1
        while True:
            params = {
                "serviceKey": API_KEY,
                "numOfRows": "100",
                "pageNo": str(page),
                "resultType": "json",
                "mrktCls": market
            }
            try:
                res = requests.get(url, params=params, timeout=10)
                data = res.json()
                items = data['response']['body']['items']['item']
                if isinstance(items, dict):
                    items = [items]
                
                for item in items:
                    rows.append({
                        'Code': item.get('srtnCd', ''),
                        'Name': item.get('itmsNm', ''),
                        'Market': market
                    })
                
                total = int(data['response']['body']['totalCount'])
                if page * 100 >= min(total, 500 if market == "KOSPI" else 1000):
                    break
                page += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"종목 리스트 오류: {e}")
                break

    df = pd.DataFrame(rows).drop_duplicates(subset=['Code'])
    print(f"✅ 총 {len(df)}개 종목 로드 완료")
    return df

# ==========================================
# 4. 메인 로직
# ==========================================
def main():
    print(f"[{TARGET_DATE}] 프로그램 시작 (한국 시간 기준)")
    print("✅ 분석을 시작합니다...")

    try:
        df_final_list = get_stock_list()

        if df_final_list.empty:
            raise Exception("종목 리스트가 비어있습니다.")

        all_analyzed = []
        total_len = len(df_final_list)
        print(f"📡 총 {total_len}개 종목 분석 시작...")

        for idx, row in df_final_list.iterrows():
            code = row['Code']
            name = row['Name']

            try:
                df = get_stock_price(code)
                if df is None or len(df) < 20:
                    continue

                current_price = df['clpr'].iloc[-1]
                ma20 = df['clpr'].rolling(window=20).mean().iloc[-1]

                if pd.isna(ma20) or ma20 == 0:
                    continue

                disparity = round((current_price / ma20) * 100, 1)
                all_analyzed.append({'name': name, 'code': code, 'disparity': disparity})

            except:
                continue

            time.sleep(0.1)

        # 계단식 필터링
        results = [r for r in all_analyzed if r['disparity'] <= 90.0]
        filter_level = "이격도 90% 이하 (초과대낙폭)"

        if not results:
            print("💡 90% 이하가 없어 95%로 범위를 넓힙니다.")
            results = [r for r in all_analyzed if r['disparity'] <= 95.0]
            filter_level = "이격도 95% 이하 (일반낙폭)"

        if results:
            results = sorted(results, key=lambda x: x['disparity'])

            report = f"### 📊 종목 분석 결과 ({filter_level})\n"
            for r in results[:40]:
                report += f"· **{r['name']}({r['code']})**: {r['disparity']}%\n"

            report += "\n" + "="*30 + "\n"
            report += "📝 **[Check List]**\n"
            report += "1. 영업이익 적자기업 제외하고 테마별로 표로 분류\n"
            report += "2. 최근 일주일간 뉴스 및 날짜 확인\n"
            report += "3. 이격도 하락 원인 분석\n"
            report += "4. 종합 판단 후 최종 종목 선정"

            send_discord_message(report)
            print(f"✅ {len(results)}개 추출 및 전송 완료.")
        else:
            send_discord_message("🔍 조건에 맞는 종목이 없습니다.")

    except Exception as e:
        err_msg = f"❌ 프로그램 오류: {e}"
        print(err_msg)
        send_discord_message(err_msg)

if __name__ == "__main__":
    main()
