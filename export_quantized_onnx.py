#!/usr/bin/env python3
"""
export_quantized_onnx.py
Sign0 / SignCodec: INT8 Post-Training Quantization (PTQ) & ONNX Opset 14 Export.
Produces high-performance INT8 quantized models for edge & CPU inference:
  1. PyTorch Dynamic Quantization (qint8)
  2. ONNX Runtime Dynamic Quantization (backend/asl_mlp_int8.onnx)
"""

import os
import sys
import torch
from asl_models import ASLClassifierV2

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

try:
    import onnx
    import onnxruntime as ort
    from onnxruntime.quantization import quantize_dynamic, QuantType
    ONNX_QUANT_AVAILABLE = True
except ImportError:
    ONNX_QUANT_AVAILABLE = False


def export_int8_models():
    os.makedirs("backend", exist_ok=True)
    device = torch.device("cpu")

    # 1. Load trained FP32 model
    model = ASLClassifierV2()
    weights_path = "best_asl_model.pth"
    if os.path.exists(weights_path):
        state_dict = torch.load(weights_path, map_location=device, weights_only=True)
        model.load_state_dict(state_dict)
        print(f" Loaded weights from {weights_path}")
    else:
        print(f" Warning: {weights_path} not found. Using initialized model weights.")
    model.eval()

    # 2. PyTorch Dynamic Quantization (INT8)
    print(" Executing PyTorch Dynamic Quantization (qint8 Linear layers)...")
    quantized_pytorch_model = torch.quantization.quantize_dynamic(
        model, {torch.nn.Linear}, dtype=torch.qint8
    )
    torch.save(quantized_pytorch_model.state_dict(), "backend/asl_mlp_pytorch_int8.pth")
    print(" Saved backend/asl_mlp_pytorch_int8.pth")

    # 3. Export FP32 ONNX model as base
    fp32_onnx_path = os.path.join("backend", "asl_mlp.onnx")
    int8_onnx_path = os.path.join("backend", "asl_mlp_int8.onnx")
    dummy_input = torch.randn(1, 63, dtype=torch.float32)

    print(" Exporting base ONNX model...")
    torch.onnx.export(
        model,
        dummy_input,
        fp32_onnx_path,
        input_names=["keypoints"],
        output_names=["logits"],
        dynamic_axes={"keypoints": {0: "batch_size"}, "logits": {0: "batch_size"}},
        opset_version=14
    )
    print(f" Exported base FP32 ONNX model: {fp32_onnx_path}")

    # 4. Perform ONNX Runtime Dynamic INT8 Quantization
    if ONNX_QUANT_AVAILABLE:
        print(" Running ONNX Runtime INT8 Post-Training Dynamic Quantization...")
        quantize_dynamic(
            model_input=fp32_onnx_path,
            model_output=int8_onnx_path,
            weight_type=QuantType.QInt8,
            per_channel=True,
            reduce_range=False
        )
        print(f" Successfully exported calibrated INT8 ONNX model: {int8_onnx_path}")
    else:
        # Fallback copy
        print(" ONNX quantization module unavailable, using exported model.")
        torch.onnx.export(
            quantized_pytorch_model,
            dummy_input,
            int8_onnx_path,
            input_names=["keypoints"],
            output_names=["logits"],
            opset_version=14
        )

    # File size comparison
    fp32_size = os.path.getsize(fp32_onnx_path) / 1024.0
    int8_size = os.path.getsize(int8_onnx_path) / 1024.0
    print(f"\n Model Compression Report:")
    print(f" • FP32 ONNX Model Size : {fp32_size:.1f} KB")
    print(f" • INT8 ONNX Model Size : {int8_size:.1f} KB")
    print(f" • Memory Reduction     : {(1.0 - int8_size / fp32_size) * 100:.1f}%\n")


if __name__ == "__main__":
    export_int8_models()
