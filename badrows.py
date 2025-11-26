import pandas as pd

df = pd.read_csv('record.csv')
bad_rows = df[~df['actionId'].astype(str).str.isnumeric()]
print(bad_rows)  # 👀 看看哪些行错了