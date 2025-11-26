import os
import csv
import torch
from torch.utils.data import Dataset
from PIL import Image
from torchvision import transforms

class CuriosityDataset(Dataset):
    def __init__(self, csv_path, screenshot_dir='screenshots'):
        self.data = []
        self.screenshot_dir = screenshot_dir
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['actionId'] != '-1':
                    self.data.append({
                        'before': os.path.join(screenshot_dir, row['s_t_img']),
                        'after': os.path.join(screenshot_dir, row['s_t1_img']),
                        'action': int(row['actionId'])
                    })

        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        before_img = self.transform(Image.open(item['before']).convert('RGB'))
        after_img = self.transform(Image.open(item['after']).convert('RGB'))
        action = torch.tensor(item['action'])
        return before_img, action, after_img