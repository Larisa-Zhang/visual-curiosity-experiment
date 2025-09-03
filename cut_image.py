import os
from PIL import Image

def crop_center(img, crop_size=500):
    """裁剪图片中心 crop_size x crop_size"""
    width, height = img.size
    if width < crop_size or height < crop_size:
        raise ValueError(f"图片太小 ({width}x{height})，无法裁剪 {crop_size}x{crop_size}")
    
    left = (width - crop_size) // 2
    top = (height - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    return img.crop((left, top, right, bottom))

def batch_crop(input_folder, output_folder, crop_size=500):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".png"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            try:
                img = Image.open(input_path)
                cropped = crop_center(img, crop_size)
                cropped.save(output_path)
                print(f"✅ 已保存: {output_path}")
            except Exception as e:
                print(f"⚠️ 跳过 {filename}: {e}")

# 使用示例
input_dir = "images"     # 原始 PNG 文件夹
output_dir = "output_pngs"   # 裁剪后 PNG 文件夹
batch_crop(input_dir, output_dir)