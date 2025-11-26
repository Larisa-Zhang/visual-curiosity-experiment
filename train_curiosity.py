# train_curiosity.py
import torch
from torch.utils.data import DataLoader
import torch.nn.functional as F
from curiosity_dataset import CuriosityDataset
from curiosity_model import Encoder, ForwardModel

dataset = CuriosityDataset('record.csv')
loader = DataLoader(dataset, batch_size=16, shuffle=True)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
encoder = Encoder().to(device)
forward_model = ForwardModel().to(device)
optim = torch.optim.Adam(list(encoder.parameters()) + list(forward_model.parameters()), lr=1e-4)

action_dim = 4

def to_one_hot(actions, num_classes=4):
    return F.one_hot(actions, num_classes=num_classes).float()

best_loss = float('inf')  # 初始为正无穷

for epoch in range(10):
    total_loss = 0
    for before, action, after in loader:
        before, after, action = before.to(device), after.to(device), action.to(device)
        
        state = encoder(before)              # shape: [B, 128]
        next_state = encoder(after)          # shape: [B, 128]
        action_onehot = to_one_hot(action, action_dim).to(device)

        predicted_next_state = forward_model(state, action_onehot)
        loss = F.mse_loss(predicted_next_state, next_state)

        optim.zero_grad()
        loss.backward()
        optim.step()

        total_loss += loss.item()
    
    avg_loss = total_loss / len(loader)
    avg_loss = avg_loss*1000
    print(f"Epoch {epoch+1} Loss: {avg_loss:.4f}")

    # ✅ 只保存效果最好的模型
    if avg_loss < best_loss:
        best_loss = avg_loss
        torch.save({
            'encoder': encoder.state_dict(),
            'forward_model': forward_model.state_dict()
        }, 'curiosity_model_best.pth')
        print(f"✅ Saved best model (Loss: {best_loss:.4f})")