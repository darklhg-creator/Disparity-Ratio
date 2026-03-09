import FinanceDataReader as fdr
import time

codes = ['005930', '000660', '035420', '051910', '006400']
start = time.time()

for code in codes:
    df = fdr.DataReader(code, '2026-01-01')
    print(f"{code}: {len(df)}일치, 최신: {df.index[-1].strftime('%Y-%m-%d')}")

end = time.time()
print(f"\n5개 종목 소요시간: {round(end-start, 1)}초")
print(f"1500개 예상시간: {round((end-start)/5*1500/60, 1)}분")
