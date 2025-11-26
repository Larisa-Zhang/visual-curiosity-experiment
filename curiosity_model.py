import torch
import torch.nn as nn

class Encoder(nn.Module):
    def __init__(self, output_dim=128):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(3, 16, 4, stride=2, padding=1),  # [B, 16, 64, 64]
            nn.ReLU(),
            nn.Conv2d(16, 32, 4, stride=2, padding=1), # [B, 32, 32, 32]
            nn.ReLU(),
            nn.Conv2d(32, 64, 4, stride=2, padding=1), # [B, 64, 16, 16]
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 16 * 16, output_dim)
        )

    def forward(self, x):
        return self.conv(x)

class ForwardModel(nn.Module):
    def __init__(self, state_dim=128, action_dim=4):  # 4 个动作
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(state_dim + action_dim, 256),
            nn.ReLU(),
            nn.Linear(256, state_dim)
        )

    def forward(self, state, action_onehot):
        x = torch.cat([state, action_onehot], dim=1)
        return self.fc(x)