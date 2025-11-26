# reinforcement_train_curiosity.py

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from curiosity_model import Encoder, ForwardModel
from curiosity_dataset import CuriosityDataset

# === 配置 ===
csv_path = 'record.csv'
image_folder = 'screenshots'
batch_size = 32
num_epochs = 10
action_dim = 4  # up/down/left/right
learning_rate = 1e-4

# === 模型定义 ===
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
encoder = Encoder().to(device)
forward_model = ForwardModel().to(device)

# === 加载已有模型参数（如果存在） ===
checkpoint_path = 'curiosity_model_best.pth'
if os.path.exists(checkpoint_path):
    print(f"🔁 Loading existing checkpoint from {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    encoder.load_state_dict(checkpoint['encoder'])
    forward_model.load_state_dict(checkpoint['forward_model'])
else:
    print("🚀 No checkpoint found, training from scratch.")

# === 优化器 ===
optimizer = torch.optim.Adam(
    list(encoder.parameters()) + list(forward_model.parameters()),
    lr=learning_rate
)

# === 数据集与 DataLoader ===
dataset = CuriosityDataset(csv_path, image_folder)
loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# === 训练 ===
best_loss = float('inf')
for epoch in range(1, num_epochs + 1):
    total_loss = 0
    for before, action, after in loader:
        before, after, action = before.to(device), after.to(device), action.to(device)

        state = encoder(before)             # [B, 128]
        next_state = encoder(after)         # [B, 128]
        action_onehot = F.one_hot(action, action_dim).float().to(device)

        predicted = forward_model(state, action_onehot)
        loss = F.mse_loss(predicted, next_state)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(loader)
    avg_loss = avg_loss*1000
    print(f"📘 Epoch {epoch} Loss: {avg_loss:.6f}")

    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save({
            'encoder': encoder.state_dict(),
            'forward_model': forward_model.state_dict()
        }, checkpoint_path)
        print(f"✅ Saved best model (Loss: {best_loss:.6f})")