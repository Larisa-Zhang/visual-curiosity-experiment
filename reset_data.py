import os
import csv

# 路径配置
SCREENSHOT_DIR = 'screenshots'
CSV_PATH = 'record.csv'

# 清空 screenshots 文件夹
def clear_screenshots():
    if os.path.exists(SCREENSHOT_DIR):
        for filename in os.listdir(SCREENSHOT_DIR):
            file_path = os.path.join(SCREENSHOT_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(f'✅ 清空 {SCREENSHOT_DIR}/ 完成')
    else:
        print(f'⚠️ 目录 {SCREENSHOT_DIR}/ 不存在')

# 重置 CSV 文件（保留表头）
def reset_csv():
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['model', 's_t_img', 'actionId', 's_t1_img'])
    print(f'✅ 重置 {CSV_PATH} 完成')

# 执行清空逻辑
if __name__ == '__main__':
    clear_screenshots()
    reset_csv()