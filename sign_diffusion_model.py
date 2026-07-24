import os
import math
import json
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ==========================================
# 1. SINUSOIDAL TIMESTEP EMBEDDING
# ==========================================
class SinusoidalPosEmb(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.dim = dim

    def forward(self, x):
        device = x.device
        half_dim = self.dim // 2
        emb = math.log(10000) / (half_dim - 1)
        emb = torch.exp(torch.arange(half_dim, device=device) * -emb)
        emb = x[:, None] * emb[None, :]
        emb = torch.cat((emb.sin(), emb.cos()), dim=-1)
        return emb

# ==========================================
# 2. TEXT-CONDITIONED KEYPOINT DENOISING NETWORK
# ==========================================
class SignDiffusionSynthesizer(nn.Module):
    """
    Denoising Diffusion Probabilistic Model (DDPM) for 3D Hand Landmark Sequence Generation.
    Input:
      - x_t: Noisy keypoint sequence (Batch, Seq_Len, 63)
      - timesteps: Diffusion step indices (Batch,)
      - text_ids: Token indices for input prompt (Batch,)
    Output:
      - Predicted Gaussian noise (Batch, Seq_Len, 63)
    """
    def __init__(self, keypoint_dim=63, seq_len=20, num_text_tokens=50, d_model=128):
        super().__init__()
        self.seq_len = seq_len
        self.keypoint_dim = keypoint_dim
        
        self.time_mlp = nn.Sequential(
            SinusoidalPosEmb(d_model),
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model)
        )
        
        self.text_emb = nn.Embedding(num_text_tokens, d_model)
        
        self.in_proj = nn.Linear(keypoint_dim, d_model)
        
        self.backbone = nn.Sequential(
            nn.Linear(d_model * 3, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Linear(256, d_model)
        )
        
        self.out_proj = nn.Linear(d_model, keypoint_dim)

    def forward(self, x_t, timesteps, text_ids):
        # x_t: (B, T, 63)
        B, T, K = x_t.shape
        
        t_emb = self.time_mlp(timesteps).unsqueeze(1).repeat(1, T, 1) # (B, T, d_model)
        c_emb = self.text_emb(text_ids).unsqueeze(1).repeat(1, T, 1)  # (B, T, d_model)
        x_emb = self.in_proj(x_t)                                    # (B, T, d_model)
        
        combined = torch.cat([x_emb, t_emb, c_emb], dim=-1)           # (B, T, d_model * 3)
        h = self.backbone(combined)
        pred_noise = self.out_proj(h)                                 # (B, T, 63)
        return pred_noise

# ==========================================
# 3. DDPM SCHEDULER & SAMPLER PIPELINE
# ==========================================
class SignDDPMPipeline:
    def __init__(self, model, num_timesteps=100, beta_start=1e-4, beta_end=0.02, device="cpu"):
        self.model = model.to(device)
        self.device = device
        self.num_timesteps = num_timesteps
        
        self.betas = torch.linspace(beta_start, beta_end, num_timesteps, device=device)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)

    def sample(self, text_id, seq_len=20, shape=(1, 20, 63)):
        self.model.eval()
        with torch.no_grad():
            x = torch.randn(shape, device=self.device)
            text_tensor = torch.tensor([text_id], dtype=torch.long, device=self.device)
            
            for t in reversed(range(self.num_timesteps)):
                t_tensor = torch.tensor([t], dtype=torch.long, device=self.device)
                predicted_noise = self.model(x, t_tensor, text_tensor)
                
                beta_t = self.betas[t]
                alpha_t = self.alphas[t]
                alpha_cumprod_t = self.alphas_cumprod[t]
                
                # Reverse step formulation
                mean = (1.0 / torch.sqrt(alpha_t)) * (x - (beta_t / torch.sqrt(1.0 - alpha_cumprod_t)) * predicted_noise)
                
                if t > 0:
                    noise = torch.randn_like(x)
                    x = mean + torch.sqrt(beta_t) * noise
                else:
                    x = mean
            return x.cpu().numpy()[0]

# ==========================================
# 4. TRAINING & SYNTHESIS GENERATOR
# ==========================================
PROMPT_VOCAB = {
    "hello": 0, "thank you": 1, "please": 2, "yes": 3, "no": 4,
    "help": 5, "i love you": 6, "water": 7, "eat": 8, "goodbye": 9
}

def train_and_export_diffusion():
    print("--> Initializing Text-Conditioned 3D Keypoint Diffusion Model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training Sign Diffusion Model on: {device}")
    
    model = SignDiffusionSynthesizer(keypoint_dim=63, seq_len=20, num_text_tokens=len(PROMPT_VOCAB) + 5, d_model=128)
    pipeline = SignDDPMPipeline(model, num_timesteps=100, device=device)
    
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.MSELoss()
    
    # Train dummy diffusion loop for 20 epochs
    print("\n--> Training Diffusion Denoising Loop...")
    start_t = time.time()
    
    for epoch in range(1, 21):
        model.train()
        total_loss = 0.0
        
        # Batch simulation over prompt vocabulary
        for prompt_name, token_id in PROMPT_VOCAB.items():
            # Create synthetic target gesture animation (20 frames, 63 keypoints)
            x_0 = torch.randn(4, 20, 63, device=device) * 0.2
            t = torch.randint(0, 100, (4,), device=device)
            
            # Add noise
            noise = torch.randn_like(x_0)
            alpha_cumprod_t = pipeline.alphas_cumprod[t].view(4, 1, 1)
            x_t = torch.sqrt(alpha_cumprod_t) * x_0 + torch.sqrt(1.0 - alpha_cumprod_t) * noise
            
            text_ids = torch.tensor([token_id] * 4, dtype=torch.long, device=device)
            
            optimizer.zero_grad()
            pred_noise = model(x_t, t, text_ids)
            loss = criterion(pred_noise, noise)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        if epoch % 5 == 0 or epoch == 20:
            print(f"Epoch {epoch:02d}/20 | Loss: {total_loss / len(PROMPT_VOCAB):.4f}")
            
    print(f"Diffusion Model Training Complete in {time.time() - start_t:.2f}s!")
    
    # Save checkpoint
    torch.save(model.state_dict(), "best_sign_diffusion.pth")
    
    # Sample and generate pre-computed animations dictionary for frontend rendering
    print("\n--> Pre-computing 3D Landmark Animations for Prompt Library...")
    synthesis_library = {}
    for prompt_name, token_id in PROMPT_VOCAB.items():
        sample_anim = pipeline.sample(token_id, seq_len=20)
        # Reshape to (20 frames, 21 joints, 3 coordinates)
        frames_3d = sample_anim.reshape(20, 21, 3).tolist()
        synthesis_library[prompt_name] = frames_3d
        
    library_path = os.path.join("backend", "sign_diffusion_library.json")
    with open(library_path, "w") as f:
        json.dump(synthesis_library, f, indent=2)
        
    print(f"SUCCESS: Precomputed Diffusion Animations exported to {library_path}")

if __name__ == "__main__":
    train_and_export_diffusion()
