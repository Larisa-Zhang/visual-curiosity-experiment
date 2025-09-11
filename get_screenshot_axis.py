import csv
import shutil
import os
model_list = {}
i=0
with open("record.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:

        model_name = row[1]
        if model_name == 'model':
            continue
        action_id = row[2]
        s_t_img = row[3]
        s_t1_img = row[4]
        after_yaw = row[5]
        after_pitch = row[6]
        delta_yaw = row[7]
        delta_pitch = row[8]
        init_yaw = row[9]
        init_pitch = row[10]
        model_name_clean = model_name.split('.')[0]
        if action_id == '-1':
            continue
        if model_name_clean in model_list:
            continue
        model_list[model_name_clean] = 1
        print(model_name_clean)
        screen_shot_name = f"{model_name_clean}${after_yaw}${after_pitch}.png"
        orig_screen_shot_name = s_t1_img
        screenshot_base_path = f"./screenshots/{s_t1_img}"
        target_path = './public/images/' + screen_shot_name
        shutil.copy(screenshot_base_path, target_path)
        i+=1
        print("文件已复制并改名:", target_path)

    print(f"Total unique models: {i}")

    