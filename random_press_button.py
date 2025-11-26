import pyautogui
import random
import time

# 按键列表（上下左右箭头）
keys = ["up", "down", "left", "right"]

# 总次数
n = 5000
time.sleep(3.3)
# 循环按键
for i in range(n):
    key = random.choice(keys)   # 随机选择一个按键
    pyautogui.press(key)        # 模拟按键
    print(f"{i+1}: 按下 {key}")  # 打印进度
    time.sleep(0.1)             # 间隔 0.3 秒