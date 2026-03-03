import FinanceDataReader as fdr
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sys

# ==========================================
# 0. 사용자 설정
# ==========================================
IGYEOK_WEBHOOK_URL = "https://discord.com/api/webhooks/1461902939139604684/ZdCdITanTb3sotd8LlCYlJzSYkVLduAsjC6CD2h26X56wXoQRw7NY72kTNzxTI6UE4Pi"

KST_TIMEZONE = timezone(timedelta(hours=9))
CURRENT_KST = datetime.now(KST_TIMEZONE)
TARGET_DATE = CURRENT_KST.strftime("%Y-%m-%d")

# ==========================================
# 1. 공통 함수
# ==========================================
def send_discord_message(content):
    try:
        data = {'content': content}
        requests.post(IGYEOK_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

# ==========================================
# 2. 메인 로직
# ==========================================
def main():
    print(f"[{TARGET_DATE}] 프로그램 시작 (한국 시간 기준)")

    # 1. 주말 체크
    weekday = CURRENT_KST.weekday()
    if weekday >= 5:
        msg = "⏹️ 오늘은 주말이라 주식장이 열리지 않습니다."
        print(msg)
        send_discord_message(msg)
        return

    print(f"✅ 정상 개장일입니다. 분석을 시작합니다...")
    print("🚀 [1단계] 계단식 이격도 분석 시작 (KRX 통합 리스트 활용)")

    try:
        # [수정 포인트] 개별 호출 대신 KRX 전체를 가져와서 나눕니다.
        print("📡 종목 리스트 불러오는 중 (KRX 통합)...")
        df_krx = fdr.StockListing('KRX')
        
        # 코스피 500개, 코스닥 1000개 추출
        df_kospi = df_krx[df_krx['Market'] == 'KOSPI'].head(500)
        df_kosdaq = df_krx[df_krx['Market'] == 'KOSDAQ'].head(1000)
        df_total = pd.concat([df_kospi, df_kosdaq])

        all_analyzed = []
        total_count = len(df_total)
        print(f"📡 총 {total_count}개 종목 데이터 분석 시작...")

        for idx, row in df_total.iterrows():
            code = row['Code']
            name = row['Name']
            
            try:
                # 개별 종목 데이터 수집
                df = fdr.DataReader(code)
                if df is None or len(df) < 20:
                    continue
                
                df = df.tail(30)
                current_price = df['Close'].iloc[-1]
                ma20 = df['Close'].rolling(window=20).mean().iloc[-1]

                if pd.isna(ma20) or ma20 == 0:
                    continue

                disparity = round((current_price / ma20) * 100, 1)
                all_analyzed.append({'name': name, 'code': code, 'disparity': disparity})
            except:
                continue

        # 2. 필터링 로직
        results = [r for r in all_analyzed if r['disparity'] <= 90.0]
        filter_level = "이격도 90% 이하 (초과대낙폭)"

        if not results:
            results = [r for r in all_analyzed if r['disparity'] <= 95.0]
            filter_level = "이격도 95% 이하 (일반낙폭)"

        # 3. 결과 전송
        if results:
            results = sorted(results, key=lambda x: x['disparity'])
            report = f"### 📊 종목 분석 결과 ({filter_level})\n"
            for r in results[:30]:
                report += f"· **{r['name']}({r['code']})**: {r['disparity']}%\n"

            report += "\n📝 **[Check List]**\n1. 적자기업 제외/테마 분류\n2. 최근 뉴스 확인\n3. 하락 원인 분석\n4. 최종 종목 선정"
            
            send_discord_message(report)
            print(f"✅ 분석 완료! {len(results)}개 추출됨.")
        else:
            send_discord_message("🔍 조건에 맞는 종목이 없습니다.")

    except Exception as e:
        err_msg = f"❌ 메인 로직 에러 발생: {e}"
        print(err_msg)
        send_discord_message(err_msg)

if __name__ == "__main__":
    main()
