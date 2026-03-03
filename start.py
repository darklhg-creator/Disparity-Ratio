import FinanceDataReader as fdr
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sys
import time

# ==========================================
# 0. 사용자 설정
# ==========================================
IGYEOK_WEBHOOK_URL = os.environ.get("IGYEOK_WEBHOOK_URL", "https://discord.com/api/webhooks/1461902939139604684/ZdCdITanTb3sotd8LlCYlJzSYkVLduAsjC6CD2h26X56wXoQRw7NY72kTNzxTI6UE4Pi")

# [한국 시간 설정]
KST_TIMEZONE = timezone(timedelta(hours=9))
CURRENT_KST = datetime.now(KST_TIMEZONE)
TARGET_DATE = CURRENT_KST.strftime("%Y-%m-%d")

# ==========================================
# 1. 공통 함수
# ==========================================
def send_discord_message(content):
    try:
        if len(content) <= 2000:
            requests.post(IGYEOK_WEBHOOK_URL, json={'content': content}, timeout=10)
        else:
            for i in range(0, len(content), 2000):
                requests.post(IGYEOK_WEBHOOK_URL, json={'content': content[i:i+2000]}, timeout=10)
                time.sleep(0.5)
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

def get_market_indices():
    try:
        kospi = fdr.DataReader('^KS11', start='2024-01-01')
        kosdaq = fdr.DataReader('^KQ11', start='2024-01-01')
        
        def calc_disp(df):
            if df.empty or len(df) < 20: return 0, 0, 0
            curr = df['Close'].iloc[-1]
            d = round((curr / df['Close'].rolling(20).mean().iloc[-1]) * 100, 1)
            w = round((curr / df.resample('W').last()['Close'].rolling(20).mean().iloc[-1]) * 100, 1)
            m = round((curr / df.resample('ME').last()['Close'].rolling(20).mean().iloc[-1]) * 100, 1)
            return d, w, m
        
        return calc_disp(kospi), calc_disp(kosdaq)
    except:
        return (0,0,0), (0,0,0)

# ==========================================
# 2. 메인 로직
# ==========================================
def main():
    print(f"[{TARGET_DATE}] 프로그램 시작 (한국 시간 기준)")

    # [1] 휴장일 체크
    weekday = CURRENT_KST.weekday()
    if weekday >= 5:
        msg = "⏹️ 오늘은 주말이라 분석을 쉬어갑니다."
        print(msg)
        send_discord_message(msg)
        return

    # [2] 시장 지수 및 종목 리스트 수집
    kp, kq = get_market_indices()

    print("📡 종목 리스트 수집 중 (KRX)...")
    try:
        # KRX 전체 리스트 수집 시도 (재시도 로직 포함)
        df_krx = None
        for i in range(3): # 최대 3번 시도
            try:
                df_krx = fdr.StockListing('KRX')
                if not df_krx.empty: break
            except:
                print(f"재시도 중... ({i+1}/3)")
                time.sleep(2)

        if df_krx is None or df_krx.empty:
            raise ValueError("KRX 데이터를 가져올 수 없습니다. 서버 응답 오류.")

    except Exception as e:
        # KRX 실패 시 대안: KOSPI/KOSDAQ 개별 시도
        print(f"⚠️ KRX 통합 수집 실패: {e}. KOSPI 리스트로 대체 시도합니다.")
        try:
            df_krx = fdr.StockListing('KOSPI')
        except:
            raise Exception("모든 종목 리스트 수집 방법이 실패했습니다.")

    # 분석 대상 필터링
    stocks = df_krx[df_krx['Market'].isin(['KOSPI', 'KOSDAQ'])].head(1000)

    # [3] 개별 종목 분석
    all_analyzed = []
    print(f"🚀 분석 시작 (대상: {len(stocks)}개)")

    for _, row in stocks.iterrows():
        try:
            code, name = row['Code'], row['Name']
            # 주가 데이터 가져올 때 타임아웃 방지
            df = fdr.DataReader(code).tail(30)
            if len(df) < 20: continue

            current_price = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            
            if ma20 == 0 or pd.isna(ma20): continue
            
            disparity = round((current_price / ma20) * 100, 1)
            all_analyzed.append({'name': name, 'code': code, 'disparity': disparity})
            
        except:
            continue

    # [4] 결과 필터링 및 리포트
    results = [r for r in all_analyzed if r['disparity'] <= 90.0]
    filter_level = "이격도 90% 이하"

    if len(results) < 5:
        results = [r for r in all_analyzed if r['disparity'] <= 95.0]
        filter_level = "이격도 95% 이하"

    if results:
        results = sorted(results, key=lambda x: x['disparity'])
        report = f"### 🌍 KRX 분석 결과 ({TARGET_DATE})\n"
        report += f"**[시장 이격]** 코스피:{kp[0]}% / 코스닥:{kq[0]}%\n\n"
        report += f"### 🎯 추출 종목 ({filter_level})\n"
        
        for r in results[:40]:
            report += f"· **{r['name']}({r['code']})**: {r['disparity']}%\n"

        send_discord_message(report)
        print(f"✅ 리포트 전송 완료")
    else:
        print("🔍 조건에 맞는 종목이 없습니다.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err_msg = f"❌ 시스템 오류 발생: {e}"
        print(err_msg)
        send_discord_message(err_msg)
