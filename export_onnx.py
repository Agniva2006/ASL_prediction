import os
import torch
import torch.nn as nn

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class ASLClassifierV2(nn.Module):
    def __init__(self, input_dim=63, num_classes=26):
        super().__init__()
        self.in_proj = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.2)
        )
        
        self.block1 = nn.Sequential(
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(256, 256),
            nn.LayerNorm(256),
            nn.GELU()
        )
        
        self.block2 = nn.Sequential(
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(128, 128),
            nn.LayerNorm(128),
            nn.GELU()
        )
        
        self.head = nn.Linear(128, num_classes)
        
    def forward(self, x):
        h = self.in_proj(x)
        h = h + self.block1(h)
        h2 = self.block2(h)
        return self.head(h2)

def export():
    device = torch.device("cpu")
    model = ASLClassifierV2()
    state_dict = torch.load("best_asl_model.pth", map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    dummy_input = torch.randn(1, 63, dtype=torch.float32)
    onnx_path = os.path.join("backend", "asl_mlp.onnx")

    try:
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["keypoints"],
            output_names=["logits"],
            dynamic_axes={
                "keypoints": {0: "batch_size"},
                "logits": {0: "batch_size"}
            },
            opset_version=14,
            dynamo=False
        )
        print(f"ONNX Model exported successfully to {onnx_path}")
    except Exception as e:
        print(f"ONNX export with dynamo=False failed: {e}. Trying legacy export...")
        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["keypoints"],
            output_names=["logits"],
            opset_version=12
        )
        print(f"Legacy ONNX export successful to {onnx_path}")

if __name__ == "__main__":
    export()
