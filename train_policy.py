import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from policy_model import PolicyNetwork
from curiosity_model import Encoder
import pandas as pd
from PIL import Image
from torchvision import transforms
import os
import pandas as pd
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
# Dataset
import os
import pandas as pd
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
class PolicyDataset(Dataset):
    def __init__(self, csv_path, img_dir, normalize_reward=True):
        self.img_dir = img_dir
        self.df = pd.read_csv(csv_path)

        # ✅ 只保留有效数据：非初始化行，图像名存在，reward 是数字
        self.df = self.df[
            (self.df['actionId'] != -1) &
            (self.df['s_t_img'].notnull()) &
            (self.df['reward'].notnull())
        ].reset_index(drop=True)

        # ✅ 图像预处理
        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
        ])

        # ✅ 是否使用标准化 reward
        self.normalize_reward = normalize_reward
        if self.normalize_reward:
            self.raw_rewards = self.df['reward'].values.astype(np.float32)
            self.mean = np.mean(self.raw_rewards)
            self.std = np.std(self.raw_rewards)

            # 避免除以 0
            if self.std < 1e-8:
                self.std = 1.0

            # 添加新列（可选，仅用于 debug）
            self.df['normalized_reward'] = (self.df['reward'] - self.mean) / self.std

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        try:
            img_path = os.path.join(self.img_dir, row['s_t_img'])
            image = Image.open(img_path).convert('RGB')
            image = self.transform(image)
        except Exception as e:
            print(f"⚠️ Failed to load image {img_path}: {e}")
            return self.__getitem__((idx + 1) % len(self.df))

        try:
            action = int(row['actionId'])
            reward = float(row['reward'])

            if self.normalize_reward:
                reward = (reward - self.mean) / self.std

        except Exception as e:
            print(f"⚠️ Invalid label in row {idx}: {e}")
            return self.__getitem__((idx + 1) % len(self.df))

        return image, action, reward
# Init
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
encoder = Encoder().to(device)
encoder.load_state_dict(torch.load('curiosity_model_best.pth', map_location=device)['encoder'])
encoder.eval()

policy = PolicyNetwork().to(device)
optimizer = torch.optim.Adam(policy.parameters(), lr=1e-4)

# Data
dataset = PolicyDataset('record.csv', 'screenshots')
loader = DataLoader(dataset, batch_size=32, shuffle=True)

# Train
for epoch in range(10):
    total_loss = 0
    for imgs, actions, rewards in loader:
        imgs, actions, rewards = imgs.to(device), actions.to(device), rewards.to(device)

        with torch.no_grad():
            state = encoder(imgs)

        logits = policy(state)
        log_probs = F.log_softmax(logits, dim=1)
        selected_log_probs = log_probs[range(len(actions)), actions]
        entropy = -torch.sum(log_probs * torch.exp(log_probs), dim=1).mean()
        loss = -(selected_log_probs * rewards).mean() - 0.01 * entropy

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    print(f"Epoch {epoch+1} Policy Loss: {total_loss / len(loader):.4f}")

torch.save(policy.state_dict(), 'policy_model.pth')