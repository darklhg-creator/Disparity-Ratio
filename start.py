import FinanceDataReader as fdr

df = fdr.DataReader('156100', '2026-02-01')
print(df.tail(5))
print("최신날짜:", df.index[-1])
