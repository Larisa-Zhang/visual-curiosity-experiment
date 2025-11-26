import pandas as pd
import matplotlib.pyplot as plt

# 1. 读取你记录的交互数据文件（包括 reward）
df = pd.read_csv('record.csv')  # 或 'reward_record.csv'，看你实际保存的文件名

# 2. 过滤掉没有 reward 的行（可能是初始化 actionId=-1 的行）
df = df[df['reward'].notna()]


from collections import Counter
action_counts = Counter(df['actionId'])
print(action_counts)


# 3. 可视化 reward 分布
plt.hist(df['reward'], bins=50, color='skyblue', edgecolor='black')
plt.title('Reward Distribution')
plt.xlabel('Reward')
plt.ylabel('Frequency')
plt.grid(True)
plt.show()