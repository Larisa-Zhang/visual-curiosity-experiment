import pandas as pd

# 读取 CSV
df = pd.read_csv("wifi_signals.csv")

# 按 location 和 BSSID 去重（保留第一条记录）
df_unique = df.drop_duplicates(subset=["Location", "BSSID"])

# 保存去重后的结果
df_unique.to_csv("wifi_data_dedup.csv", index=False)

# 基于 location 计数
counts = df_unique.groupby("Location")["BSSID"].nunique().reset_index()
counts.columns = ["Location", "Unique_AP_Count"]

# 保存统计结果
counts.to_csv("wifi_location_counts.csv", index=False)

print("去重后的数据保存在 wifi_data_dedup.csv")
print("统计结果保存在 wifi_location_counts.csv")
print(counts)