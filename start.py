import FinanceDataReader as fdr
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import sys
import json

# ==========================================
# 0. 사용자 설정
# ==========================================
IGYEOK_WEBHOOK_URL = "https://discord.com/api/webhooks/1461902939139604684/ZdCdITanTb3sotd8LlCYlJzSYkVLduAsjC6CD2h26X56wXoQRw7NY72kTNzxTI6UE4Pi"

# [한국 시간 설정]
KST_TIMEZONE = timezone(timedelta(hours=9))
CURRENT_KST = datetime.now(KST_TIMEZONE)
TARGET_DATE = CURRENT_KST.strftime("%Y-%m-%d")

# ==========================================
# 1. 공통 함수
# ==========================================
def send_discord_message(content):
    """디스코드 메시지 전송 함수 (에러 방지 로직 추가)"""
    try:
        data = {'content': content}
        # 디스코드는 성공 시 빈 값을 주기도 하므로, 응답 처리를 안전하게 합니다.
        response = requests.post(IGYEOK_WEBHOOK_URL, json=data)
        
        # 상태 코드가 400 이상이면 에러 출력
        if response.status_code >= 400:
            print(f"디스코드 전송 실패 (상태 코드: {response.status_code})")
            print(f"응답 내용: {response.text}")
    except Exception as e:
        print(f"디스코드 연결 예외 발생: {e}")

# ==========================================
# 2. 메인 로직
# ==========================================
def main():
    print(f"[{TARGET_DATE}] 프로그램 시작 (한국 시간 기준)")

    # 1. 주말 체크
    weekday = CURRENT_KST.weekday()
    if weekday >= 5:
        day_name = "토요일" if weekday == 5 else "일요일"
        msg = f"⏹️ 오늘은 주말({day_name})이라 주식장이 열리지 않습니다."
        print(msg)
        send_discord_message(msg)
        return # sys.exit() 대신 return 사용 권장

    print(f"✅ 정상 개장일입니다. 분석을 시작합니다...")

    print("🚀 [1단계] 계단식 이격도 분석 시작 (KOSPI 500 + KOSDAQ 1000)")

    try:
        # 1. 대상 종목 리스트 확보
        print("📡 종목 리스트 불러오는 중...")
        df_kospi = fdr.StockListing('KOSPI').head(500)
        df_kosdaq = fdr.StockListing('KOSDAQ').head(1000)
        df_total = pd.concat([df_kospi, df_kosdaq])

        all_analyzed = []
        total_count = len(df_total)
        print(f"📡 총 {total_count}개 종목 데이터 수집 시작...")

        for idx, row in df_total.iterrows():
            code = row['Code']
            name = row['Name']
            
            # 진행 상황 출력 (너무 조용하면 멈춘 것 같으므로)
            if idx % 100 == 0:
                print(f"계산 중... ({idx}/{total_count})")
                
            try:
                # 데이터 수집 시 오류 방지를 위해 에러 처리 강화
                df = fdr.DataReader(code)
                if df is None or len(df) < 20: 
                    continue
                
                df = df.tail(30)
                current_price = df['Close'].iloc[-1]
                ma20 = df['Close'].rolling(window=20).mean().iloc[-1]

                if ma20 == 0 or pd.isna(ma20): 
                    continue

                disparity = round((current_price / ma20) * 100, 1)
                all_analyzed.append({'name': name, 'code': code, 'disparity': disparity})
            except:
                continue

        # 2. 계단식 필터링 로직
        results = [r for r in all_analyzed if r['disparity'] <= 90.0]
        filter_level = "이격도 90% 이하 (초과대낙폭)"

        if not results:
            print("💡 이격도 90% 이하 종목이 없어 범위를 95%로 확대합니다.")
            results = [r for r in all_analyzed if r['disparity'] <= 95.0]
            filter_level = "이격도 95% 이하 (일반낙폭)"

        # 3. 결과 처리 및 전송
        if results:
            results = sorted(results, key=lambda x: x['disparity'])

            report = f"### 📊 종목 분석 결과 ({filter_level})\n"
            # 디스코드 글자수 제한(2000자) 고려하여 상위 30개로 조정 제안
            for r in results[:30]: 
                report += f"· **{r['name']}({r['code']})**: {r['disparity']}%\n"

            report += "\n" + "="*30 + "\n"
            report += "📝 **[Check List]**\n"
            report += "1. 영업이익 적자기업 제외하고 테마별로 표로 분류\n"
            report += "2. 최근 일주일간 뉴스 및 날짜 확인\n"
            report += "3. 이격도 하락 원인 분석\n"
            report += "4. 종합 판단 후 최종 종목 선정\n"

            send_discord_message(report)

            # targets.txt 저장
            with open("targets.txt", "w", encoding="utf-8") as f:
                lines = [f"{r['code']},{r['name']}" for r in results]
                f.write("\n".join(lines))

            print(f"✅ 분석 완료! {len(results)}개 추출됨.")
        else:
            msg = "🔍 조건에 해당되는 종목이 없습니다."
            print(msg)
            send_discord_message(msg)

    except Exception as e:
        err_msg = f"❌ 메인 로직 에러 발생: {e}"
        print(err_msg)
        # 에러 발생 시에도 디스코드에 알림
        send_discord_message(err_msg)

if __name__ == "__main__":
    main()
