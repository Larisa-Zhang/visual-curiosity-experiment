import os

# 设置模型文件夹路径
models_dir = './images'  # 你可以改成你实际的路径，比如 './public/models'

# 获取 .glb 和 .gltf 文件
model_files = [f for f in os.listdir(models_dir) if f.endswith(('.png', '.gltf'))]

# 输出为 JavaScript 数组格式
print('const modelList = [')
for f in model_files:
    print(f"  '{f.split('.')[0]}.glb',")
print('];')