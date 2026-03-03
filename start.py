import FinanceDataReader as fdr
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sys
import time

# ==========================================
# 0. 사용자 설정 및 환경 변수 체크
# ==========================================
# GitHub Secrets에 등록한 URL을 우선 사용하고, 없을 경우 제공해주신 URL을 기본값으로 사용합니다.
IGYEOK_WEBHOOK_URL = os.environ.get("IGYEOK_WEBHOOK_URL")
if not IGYEOK_WEBHOOK_URL or not IGYEOK_WEBHOOK_URL.startswith("http"):
    IGYEOK_WEBHOOK_URL = "https://discord.com/api/webhooks/1461902939139604684/ZdCdITanTb3sotd8LlCYlJzSYkVLduAsjC6CD2h26X56wXoQRw7NY72kTNzxTI6UE4Pi"

KST_TIMEZONE = timezone(timedelta(hours=9))
CURRENT_KST = datetime.now(KST_TIMEZONE)
TARGET_DATE = CURRENT_KST.strftime("%Y-%m-%d")

# ==========================================
# 1. 공통 함수
# ==========================================
def send_discord_message(content):
    try:
        # URL 검증
        if not IGYEOK_WEBHOOK_URL.startswith("http"):
            print("❌ 디스코드 URL 설정이 잘못되었습니다.")
            return

        if len(content) <= 2000:
            requests.post(IGYEOK_WEBHOOK_URL, json={'content': content}, timeout=15)
        else:
            for i in range(0, len(content), 2000):
                requests.post(IGYEOK_WEBHOOK_URL, json={'content': content[i:i+2000]}, timeout=15)
                time.sleep(0.5)
    except Exception as e:
        print(f"디스코드 전송 실패: {e}")

def get_market_indices():
    """지수 데이터는 야후(Yahoo) 소스를 사용하여 차단 가능성을 낮춤"""
    try:
        kospi = fdr.DataReader('^KS11', start='2025-01-01')
        kosdaq = fdr.DataReader('^KQ11', start='2025-01-01')
        
        def calc_disp(df):
            if df.empty or len(df) < 20: return 0, 0, 0
            curr = df['Close'].iloc[-1]
            d = round((curr / df['Close'].rolling(20).mean().iloc[-1]) * 100, 1)
            return d, 0, 0 # 단순화
        
        return calc_disp(kospi)[0], calc_disp(kosdaq)[0]
    except:
        return 0, 0

# ==========================================
# 2. 메인 로직
# ==========================================
def main():
    print(f"[{TARGET_DATE}] 프로그램 시작")

    # [1] 시장 지수 확인 (전체 흐름 파악용)
    kp_disp, kq_disp = get_market_indices()

    # [2] 종목 리스트 수집 (차단 시 대안 로직)
    print("📡 종목 리스트 수집 중...")
    df_stocks = None
    
    try:
        # 시도 1: KRX 전체 리스트
        df_stocks = fdr.StockListing('KRX')
    except Exception as e:
        print(f"⚠️ KRX 서버 차단됨. KOSPI 리스트로 재시도...")
        try:
            # 시도 2: KOSPI 리스트
            df_stocks = fdr.StockListing('KOSPI')
        except:
            print(f"❌ 모든 실시간 수집 실패. 시가총액 상위 핵심 종목으로 수동 분석을 시도합니다.")
            # 시도 3: 수동 리스트 (가장 확실한 대안 - S&P 500 고도화 시에도 활용 가능)
            manual_codes = ['005930', '000660', '035420', '035720', '005380', '005490', '036570', '012330', '068270', '006400']
            df_stocks = pd.DataFrame({'Code': manual_codes, 'Name': ['삼성전자', 'SK하이닉스', 'NAVER', '카카오', '현대차', 'POSCO홀딩스', '엔씨소프트', '현대모비스', '셀트리온', '삼성SDI']})

    # [3] 이격도 분석
    all_analyzed = []
    print(f"🚀 분석 시작 (대상: 약 {len(df_stocks)}개 종목)")

    # GitHub Actions 속도를 위해 상위 일부만 우선 분석하거나 루프 최적화
    for idx, row in df_stocks.head(500).iterrows(): # 우선 500개만 테스트
        try:
            code, name = row['Code'], row['Name']
            df = fdr.DataReader(code).tail(25)
            if len(df) < 20: continue

            curr = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            if ma20 == 0 or pd.isna(ma20): continue
            
            disp = round((curr / ma20) * 100, 1)
            all_analyzed.append({'name': name, 'code': code, 'disp': disp})
        except:
            continue
        if idx % 50 == 0: print(f"진행 중... ({idx}/{len(df_stocks)})")

    # [4] 결과 필터링 및 전송
    results = [r for r in all_analyzed if r['disp'] <= 95.0]
    
    if results:
        results = sorted(results, key=lambda x: x['disp'])
        report = f"### 📊 KRX 분석 리포트 ({TARGET_DATE})\n"
        report += f"**[시장 이격]** 코스피: {kp_disp}% / 코스닥: {kq_disp}%\n\n"
        report += f"🎯 **이격도 95% 이하 종목** (상위 30개):\n"
        for r in results[:30]:
            report += f"· {r['name']}({r['code']}): **{r['disp']}%**\n"
        
        send_discord_message(report)
        print("✅ 리포트 전송 완료")
    else:
        send_discord_message(f"🔍 {TARGET_DATE} 분석 결과, 조건에 맞는 종목이 없습니다.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_discord_message(f"❌ 최종 시스템 오류: {e}")
